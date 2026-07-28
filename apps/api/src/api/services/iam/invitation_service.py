"""
EAIMOS IAM Invitation Service (Sprint 2)
==========================================
Manages the full organization invitation lifecycle:
send (with duplicate detection), accept (creates UserOrganization membership),
reject, cancel, resend (new token + reset expiry), and paginated listing.
"""

import logging
import secrets
import uuid
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from api.models.membership import OrganizationInvitation, UserOrganization, UserRole as MembershipRole
from api.repositories.iam_repository import OrganizationInvitationRepository
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterOperator, FilterParam
from api.services.base import (
    ConflictError,
    NotFoundError,
    ServiceContext,
    ServiceResult,
)
from api.services.base.service_exceptions import BusinessRuleViolation
from api.services.iam.cache_keys import (
    INVITATION_KEY_TTL,
    invitation_by_id_cache_key,
    invitation_by_token_cache_key,
    org_invitations_list_key,
)
from api.services.iam.constants import INVITE_EXPIRY_HOURS, INVITE_TOKEN_BYTES
from api.services.iam.dtos import (
    AcceptInvitationDTO,
    InvitationListDTO,
    InvitationResponseDTO,
    InvitationSummaryDTO,
    SendInvitationDTO,
)
from api.services.iam.events import (
    InvitationAccepted,
    InvitationCancelled,
    InvitationRejected,
    InvitationResent,
    InvitationSent,
)
from api.services.iam.mappers import (
    invitation_to_response_dto,
    invitation_to_summary_dto,
    invitations_to_summary_list,
)
from api.services.iam.policies import InvitationPolicy
from api.services.iam.validators import (
    validate_invitation_not_accepted,
    validate_invitation_not_expired,
    validate_invitation_not_rejected,
    validate_no_pending_invitation,
)

logger = logging.getLogger("eaimos.iam.invitation")


def _generate_invitation_token() -> str:
    """Generate a cryptographically secure 128-bit URL-safe invitation token."""
    raw = secrets.token_bytes(INVITE_TOKEN_BYTES)
    return urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


class _InvitationRepository(BaseRepository[OrganizationInvitation]):
    def __init__(self) -> None:
        super().__init__(OrganizationInvitation)


class InvitationService:
    """
    Enterprise IAM Invitation Domain Service.

    Enforces the invitation state machine:
    PENDING → ACCEPTED (creates membership)
    PENDING → REJECTED
    PENDING → CANCELLED (admin action)
    PENDING → EXPIRED (time-based)
    PENDING → PENDING (resend = new token)
    """

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        authorizer: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
    ) -> None:
        from api.services.base.dependency_provider import container
        self.uow_service = uow_service or container.create_uow_service()
        self.cache = cache_manager or container.cache
        self.authorizer = authorizer or container.authorizer
        self.dispatcher = dispatcher or container.dispatcher

    # ─── Send ─────────────────────────────────────────────────────────────────

    async def send_invitation(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: SendInvitationDTO,
    ) -> ServiceResult[InvitationResponseDTO]:
        """
        Issue an organization invitation.
        Validates uniqueness of pending invitations for the same email+org pair.
        """
        try:
            InvitationPolicy.can_send(self.authorizer, ctx, org_id)

            org_uuid = uuid.UUID(str(org_id))
            clean_email = dto.email.lower().strip()
            token = _generate_invitation_token()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=dto.expiry_hours)

            async with self.uow_service:
                repo = _InvitationRepository()

                # Duplicate pending invitation check
                pending = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="organization_id", operator=FilterOperator.EQ, value=org_uuid),
                        FilterParam(field="email", operator=FilterOperator.EQ, value=clean_email),
                        FilterParam(field="is_accepted", operator=FilterOperator.EQ, value=False),
                        FilterParam(field="is_rejected", operator=FilterOperator.EQ, value=False),
                    ],
                )
                validate_no_pending_invitation(pending is not None, clean_email, str(org_id))

                invitation_data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    "invited_by": ctx.get_user_id_str(),
                    "email": clean_email,
                    "role": dto.role,
                    "token": token,
                    "message": dto.message,
                    "is_accepted": False,
                    "is_rejected": False,
                    "expires_at": expires_at,
                }

                invitation = await repo.create(
                    session=self.uow_service.session,
                    obj_in=invitation_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    InvitationSent(
                        aggregate_id=str(invitation.id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        invitation_id=str(invitation.id),
                        invitee_email=clean_email,
                        role=dto.role,
                        payload={"email": clean_email, "role": dto.role, "org_id": str(org_id)},
                    )
                )

            # Cache the new invitation by token and ID
            response = invitation_to_response_dto(invitation)
            await self.cache.set(
                invitation_by_token_cache_key(token),
                response.model_dump(mode="json"),
                ttl=INVITATION_KEY_TTL,
            )
            await self.cache.delete(org_invitations_list_key(org_id))

            logger.info(
                "Invitation sent",
                extra={"email": clean_email, "org_id": str(org_id), "correlation_id": ctx.correlation_id},
            )
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"send_invitation failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Accept ───────────────────────────────────────────────────────────────

    async def accept_invitation(
        self,
        ctx: ServiceContext,
        dto: AcceptInvitationDTO,
    ) -> ServiceResult[InvitationResponseDTO]:
        """
        Accept an invitation by token.
        Creates the UserOrganization membership record.
        """
        try:
            InvitationPolicy.can_accept(self.authorizer, ctx)

            async with self.uow_service:
                inv_repo = _InvitationRepository()
                invitation = await inv_repo.find_one(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="token", operator=FilterOperator.EQ, value=dto.token)],
                )
                if not invitation:
                    return ServiceResult.fail(
                        error="Invitation token is invalid or does not exist.",
                        error_code="INVITATION_NOT_FOUND",
                        status_code=404,
                    )

                validate_invitation_not_accepted(invitation.is_accepted, str(invitation.id))
                validate_invitation_not_rejected(invitation.is_rejected, str(invitation.id))
                validate_invitation_not_expired(invitation.expires_at, str(invitation.id))

                now = datetime.now(timezone.utc)

                # Mark invitation as accepted
                accepted = await inv_repo.update(
                    session=self.uow_service.session,
                    id=invitation.id,
                    obj_in={
                        "is_accepted": True,
                        "accepted_at": now,
                    },
                    actor_id=ctx.get_user_id_uuid(),
                )

                # Create membership
                membership_data: Dict[str, Any] = {
                    "user_id": ctx.get_user_id_str(),
                    "organization_id": str(invitation.organization_id),
                    "role": invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
                    "is_primary": False,
                    "joined_at": now,
                    "invited_by": str(invitation.invited_by) if invitation.invited_by else None,
                }

                membership_repo = BaseRepository[UserOrganization](UserOrganization)
                membership = await membership_repo.create(
                    session=self.uow_service.session,
                    obj_in=membership_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    InvitationAccepted(
                        aggregate_id=str(invitation.id),
                        tenant_id=str(invitation.organization_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        invitation_id=str(invitation.id),
                        invitee_email=invitation.email,
                        new_user_id=ctx.get_user_id_str() or "",
                        membership_id=str(membership.id),
                        payload={"invitation_id": str(invitation.id), "user_id": ctx.get_user_id_str()},
                    )
                )

            # Invalidate caches
            await self.cache.delete(invitation_by_token_cache_key(dto.token))
            await self.cache.delete(invitation_by_id_cache_key(invitation.id))
            await self.cache.delete(org_invitations_list_key(invitation.organization_id))

            return ServiceResult.ok(data=invitation_to_response_dto(accepted))

        except Exception as exc:
            logger.error(f"accept_invitation failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Reject ───────────────────────────────────────────────────────────────

    async def reject_invitation(
        self,
        ctx: ServiceContext,
        token: str,
    ) -> ServiceResult[bool]:
        """Mark an invitation as rejected by the invitee."""
        try:
            InvitationPolicy.can_accept(self.authorizer, ctx)  # Any authenticated user can reject their own invite

            async with self.uow_service:
                repo = _InvitationRepository()
                invitation = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="token", operator=FilterOperator.EQ, value=token)],
                )
                if not invitation:
                    return ServiceResult.fail(
                        error="Invitation token is invalid.",
                        error_code="INVITATION_NOT_FOUND",
                        status_code=404,
                    )

                validate_invitation_not_accepted(invitation.is_accepted, str(invitation.id))
                validate_invitation_not_rejected(invitation.is_rejected, str(invitation.id))

                await repo.update(
                    session=self.uow_service.session,
                    id=invitation.id,
                    obj_in={"is_rejected": True},
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    InvitationRejected(
                        aggregate_id=str(invitation.id),
                        tenant_id=str(invitation.organization_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        invitation_id=str(invitation.id),
                        invitee_email=invitation.email,
                        payload={"invitation_id": str(invitation.id)},
                    )
                )

            await self.cache.delete(invitation_by_token_cache_key(token))
            await self.cache.delete(invitation_by_id_cache_key(invitation.id))
            await self.cache.delete(org_invitations_list_key(invitation.organization_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"reject_invitation failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Cancel ───────────────────────────────────────────────────────────────

    async def cancel_invitation(
        self,
        ctx: ServiceContext,
        invitation_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]:
        """Admin cancels a pending invitation before it is accepted."""
        try:
            async with self.uow_service:
                repo = _InvitationRepository()
                invitation = await repo.get_by_id(
                    session=self.uow_service.session,
                    id=invitation_id,
                )
                if not invitation:
                    return ServiceResult.fail(
                        error=f"Invitation '{invitation_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                InvitationPolicy.can_cancel(
                    self.authorizer,
                    ctx,
                    org_id=invitation.organization_id,
                    invited_by=invitation.invited_by,
                )
                validate_invitation_not_accepted(invitation.is_accepted, str(invitation_id))

                await repo.soft_delete(
                    session=self.uow_service.session,
                    id=invitation_id,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    InvitationCancelled(
                        aggregate_id=str(invitation_id),
                        tenant_id=str(invitation.organization_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        invitation_id=str(invitation_id),
                        invitee_email=invitation.email,
                        cancelled_by=ctx.get_user_id_str(),
                        payload={"invitation_id": str(invitation_id)},
                    )
                )

            await self.cache.delete(invitation_by_token_cache_key(invitation.token))
            await self.cache.delete(invitation_by_id_cache_key(invitation_id))
            await self.cache.delete(org_invitations_list_key(invitation.organization_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"cancel_invitation failed for {invitation_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Resend ───────────────────────────────────────────────────────────────

    async def resend_invitation(
        self,
        ctx: ServiceContext,
        invitation_id: Union[uuid.UUID, str],
    ) -> ServiceResult[InvitationResponseDTO]:
        """Re-issue a fresh token and reset expiry for an existing pending invitation."""
        try:
            async with self.uow_service:
                repo = _InvitationRepository()
                invitation = await repo.get_by_id(
                    session=self.uow_service.session,
                    id=invitation_id,
                )
                if not invitation:
                    return ServiceResult.fail(
                        error=f"Invitation '{invitation_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                InvitationPolicy.can_cancel(
                    self.authorizer,
                    ctx,
                    org_id=invitation.organization_id,
                    invited_by=invitation.invited_by,
                )
                validate_invitation_not_accepted(invitation.is_accepted, str(invitation_id))
                validate_invitation_not_rejected(invitation.is_rejected, str(invitation_id))

                new_token = _generate_invitation_token()
                new_expires = datetime.now(timezone.utc) + timedelta(hours=INVITE_EXPIRY_HOURS)

                old_token = invitation.token
                updated = await repo.update(
                    session=self.uow_service.session,
                    id=invitation_id,
                    obj_in={"token": new_token, "expires_at": new_expires},
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    InvitationResent(
                        aggregate_id=str(invitation_id),
                        tenant_id=str(invitation.organization_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        invitation_id=str(invitation_id),
                        invitee_email=invitation.email,
                        payload={"invitation_id": str(invitation_id)},
                    )
                )

            # Invalidate old token cache and set new one
            await self.cache.delete(invitation_by_token_cache_key(old_token))
            await self.cache.delete(invitation_by_id_cache_key(invitation_id))
            await self.cache.delete(org_invitations_list_key(invitation.organization_id))

            return ServiceResult.ok(data=invitation_to_response_dto(updated))

        except Exception as exc:
            logger.error(f"resend_invitation failed for {invitation_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get by Token ─────────────────────────────────────────────────────────

    async def get_invitation_by_token(
        self,
        ctx: ServiceContext,
        token: str,
    ) -> ServiceResult[InvitationResponseDTO]:
        """Look up an invitation by its secure token (for claim-link views)."""
        try:
            cache_key = invitation_by_token_cache_key(token)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(
                    data=InvitationResponseDTO(**cached),
                    metadata={"cached": True},
                )

            async with self.uow_service:
                repo = _InvitationRepository()
                invitation = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="token", operator=FilterOperator.EQ, value=token)],
                )

            if not invitation:
                return ServiceResult.fail(
                    error="Invitation token is invalid or has expired.",
                    error_code="INVITATION_NOT_FOUND",
                    status_code=404,
                )

            response = invitation_to_response_dto(invitation)
            await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=INVITATION_KEY_TTL)
            return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_invitation_by_token failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── List ─────────────────────────────────────────────────────────────────

    async def list_invitations(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ServiceResult[InvitationListDTO]:
        """Return paginated invitations for an organization with optional status filter."""
        try:
            InvitationPolicy.can_list(self.authorizer, ctx, org_id)

            org_uuid = uuid.UUID(str(org_id))
            now = datetime.now(timezone.utc)

            async with self.uow_service:
                repo = _InvitationRepository()
                all_invitations = await repo.find_many(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="organization_id", operator=FilterOperator.EQ, value=org_uuid)],
                )

            # Apply status filter
            if status == "pending":
                all_invitations = [
                    i for i in all_invitations
                    if not i.is_accepted and not i.is_rejected and
                    (i.expires_at.replace(tzinfo=timezone.utc) if i.expires_at.tzinfo is None else i.expires_at) > now
                ]
            elif status == "accepted":
                all_invitations = [i for i in all_invitations if i.is_accepted]
            elif status == "rejected":
                all_invitations = [i for i in all_invitations if i.is_rejected]
            elif status == "expired":
                all_invitations = [
                    i for i in all_invitations
                    if not i.is_accepted and not i.is_rejected and
                    (i.expires_at.replace(tzinfo=timezone.utc) if i.expires_at.tzinfo is None else i.expires_at) <= now
                ]

            total = len(all_invitations)
            start = (page - 1) * page_size
            paginated = all_invitations[start: start + page_size]
            summaries = invitations_to_summary_list(paginated)

            return ServiceResult.ok(
                data=InvitationListDTO(
                    items=summaries,
                    total=total,
                    page=page,
                    page_size=page_size,
                )
            )

        except Exception as exc:
            logger.error(f"list_invitations failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
