"""
EAIMOS IAM OAuth Service (Sprint 2)
=====================================
Manages OAuth provider account linking, SSO user provisioning,
and encrypted token storage. Supports multiple providers (Google, Microsoft,
GitHub, Okta, SAML, custom enterprise SSO).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from api.models.iam import OAuthAccount
from api.models.user import User
from api.repositories.iam_repository import OAuthAccountRepository
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterOperator, FilterParam
from api.repositories.user_repository import UserRepository
from api.services.base import (
    ConflictError,
    NotFoundError,
    ServiceContext,
    ServiceResult,
)
from api.services.base.service_exceptions import BusinessRuleViolation
from api.services.iam.cache_keys import (
    OAUTH_ACCOUNT_KEY_TTL,
    oauth_account_cache_key,
    user_oauth_accounts_list_key,
)
from api.services.iam.dtos import (
    LinkOAuthAccountDTO,
    OAuthAccountResponseDTO,
    OAuthUserInfoDTO,
)
from api.services.iam.events import (
    OAuthAccountLinked,
    OAuthAccountUnlinked,
    OAuthTokenRefreshed,
    OAuthUserProvisioned,
)
from api.services.iam.mappers import (
    oauth_account_to_response_dto,
    oauth_accounts_to_response_list,
)
from api.services.iam.policies import OAuthPolicy
from api.services.iam.validators import (
    validate_oauth_account_not_already_linked,
    validate_oauth_provider_supported,
    validate_oauth_provider_user_not_taken,
)

logger = logging.getLogger("eaimos.iam.oauth")


class _OAuthAccountRepository(BaseRepository[OAuthAccount]):
    def __init__(self) -> None:
        super().__init__(OAuthAccount)


class OAuthService:
    """
    Enterprise IAM OAuth Domain Service.

    Handles:
    - Linking a provider account to an existing EAIMOS user
    - Unlinking a connected provider
    - SSO auto-provisioning: find-or-create user from OAuth profile
    - Encrypted token refresh
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

    # ─── Link OAuth Account ───────────────────────────────────────────────────

    async def link_oauth_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        dto: LinkOAuthAccountDTO,
    ) -> ServiceResult[OAuthAccountResponseDTO]:
        """
        Link an OAuth provider account to a user profile.

        Business Rules:
        - A user can have only one linked account per provider
        - A provider_user_id can only be linked to one EAIMOS user
        """
        try:
            OAuthPolicy.can_link(self.authorizer, ctx, user_id)
            validate_oauth_provider_supported(dto.provider)

            user_uuid = uuid.UUID(str(user_id))

            async with self.uow_service:
                repo = _OAuthAccountRepository()

                # Check: user doesn't already have this provider linked
                existing_for_user = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_uuid),
                        FilterParam(field="provider", operator=FilterOperator.EQ, value=dto.provider),
                    ],
                )
                validate_oauth_account_not_already_linked(
                    existing_for_user is not None,
                    str(user_id),
                    dto.provider,
                )

                # Check: provider_user_id not already used by another EAIMOS user
                existing_provider_user = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="provider", operator=FilterOperator.EQ, value=dto.provider),
                        FilterParam(field="provider_user_id", operator=FilterOperator.EQ, value=dto.provider_user_id),
                    ],
                )
                validate_oauth_provider_user_not_taken(
                    existing_provider_user is not None,
                    dto.provider,
                    dto.provider_user_id,
                )

                account_data: Dict[str, Any] = {
                    "user_id": str(user_uuid),
                    "provider": dto.provider.lower(),
                    "provider_user_id": dto.provider_user_id,
                    "access_token_encrypted": dto.access_token_encrypted,
                    "refresh_token_encrypted": dto.refresh_token_encrypted,
                    "token_expires_at": dto.token_expires_at,
                    "provider_email": dto.provider_email,
                    "provider_data": dto.provider_data or {},
                }

                account = await repo.create(
                    session=self.uow_service.session,
                    obj_in=account_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    OAuthAccountLinked(
                        aggregate_id=str(account.id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        oauth_account_id=str(account.id),
                        provider=dto.provider,
                        provider_email=dto.provider_email,
                        payload={"user_id": str(user_id), "provider": dto.provider},
                    )
                )

            # Invalidate user's oauth list cache
            await self.cache.delete(user_oauth_accounts_list_key(user_id))

            response = oauth_account_to_response_dto(account)
            # Cache the individual account
            await self.cache.set(
                oauth_account_cache_key(user_id, dto.provider),
                response.model_dump(mode="json"),
                ttl=OAUTH_ACCOUNT_KEY_TTL,
            )

            logger.info(
                "OAuth account linked",
                extra={"user_id": str(user_id), "provider": dto.provider, "correlation_id": ctx.correlation_id},
            )
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"link_oauth_account failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Unlink OAuth Account ─────────────────────────────────────────────────

    async def unlink_oauth_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        provider: str,
    ) -> ServiceResult[bool]:
        """Remove a linked OAuth account from a user profile."""
        try:
            OAuthPolicy.can_unlink(self.authorizer, ctx, user_id)
            validate_oauth_provider_supported(provider)

            user_uuid = uuid.UUID(str(user_id))
            provider_lower = provider.lower()

            async with self.uow_service:
                repo = _OAuthAccountRepository()
                account = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_uuid),
                        FilterParam(field="provider", operator=FilterOperator.EQ, value=provider_lower),
                    ],
                )
                if not account:
                    return ServiceResult.fail(
                        error=f"No '{provider}' account linked for this user.",
                        error_code="OAUTH_ACCOUNT_NOT_FOUND",
                        status_code=404,
                    )

                provider_user_id = account.provider_user_id
                await repo.hard_delete(session=self.uow_service.session, id=account.id)

                self.uow_service.add_event(
                    OAuthAccountUnlinked(
                        aggregate_id=str(account.id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        provider=provider_lower,
                        provider_user_id=provider_user_id,
                        payload={"user_id": str(user_id), "provider": provider_lower},
                    )
                )

            await self.cache.delete(oauth_account_cache_key(user_id, provider_lower))
            await self.cache.delete(user_oauth_accounts_list_key(user_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"unlink_oauth_account failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get OAuth Account ────────────────────────────────────────────────────

    async def get_oauth_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        provider: str,
    ) -> ServiceResult[OAuthAccountResponseDTO]:
        """Look up a specific linked OAuth account for a user."""
        try:
            OAuthPolicy.can_list(self.authorizer, ctx, user_id)

            provider_lower = provider.lower()
            cache_key = oauth_account_cache_key(user_id, provider_lower)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(
                    data=OAuthAccountResponseDTO(**cached),
                    metadata={"cached": True},
                )

            user_uuid = uuid.UUID(str(user_id))
            async with self.uow_service:
                repo = _OAuthAccountRepository()
                account = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_uuid),
                        FilterParam(field="provider", operator=FilterOperator.EQ, value=provider_lower),
                    ],
                )

            if not account:
                return ServiceResult.fail(
                    error=f"No '{provider}' account linked for this user.",
                    error_code="OAUTH_ACCOUNT_NOT_FOUND",
                    status_code=404,
                )

            response = oauth_account_to_response_dto(account)
            await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=OAUTH_ACCOUNT_KEY_TTL)
            return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_oauth_account failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── List User OAuth Accounts ─────────────────────────────────────────────

    async def list_user_oauth_accounts(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
    ) -> ServiceResult[List[OAuthAccountResponseDTO]]:
        """Return all OAuth accounts linked to a user."""
        try:
            OAuthPolicy.can_list(self.authorizer, ctx, user_id)

            list_cache_key = user_oauth_accounts_list_key(user_id)
            cached = await self.cache.get(list_cache_key)
            if cached is not None and isinstance(cached, list):
                return ServiceResult.ok(
                    data=[OAuthAccountResponseDTO(**a) for a in cached],
                    metadata={"cached": True},
                )

            user_uuid = uuid.UUID(str(user_id))
            async with self.uow_service:
                repo = _OAuthAccountRepository()
                accounts = await repo.find_many(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_uuid)],
                )

            responses = oauth_accounts_to_response_list(accounts)
            await self.cache.set(
                list_cache_key,
                [r.model_dump(mode="json") for r in responses],
                ttl=OAUTH_ACCOUNT_KEY_TTL,
            )
            return ServiceResult.ok(data=responses)

        except Exception as exc:
            logger.error(f"list_user_oauth_accounts failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Refresh OAuth Token ──────────────────────────────────────────────────

    async def refresh_oauth_token(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        provider: str,
        new_access_token_encrypted: str,
        new_refresh_token_encrypted: Optional[str] = None,
        new_token_expires_at: Optional[datetime] = None,
    ) -> ServiceResult[bool]:
        """Update stored encrypted tokens after provider token refresh."""
        try:
            provider_lower = provider.lower()
            user_uuid = uuid.UUID(str(user_id))

            async with self.uow_service:
                repo = _OAuthAccountRepository()
                account = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_uuid),
                        FilterParam(field="provider", operator=FilterOperator.EQ, value=provider_lower),
                    ],
                )
                if not account:
                    return ServiceResult.fail(
                        error=f"No '{provider}' account found for token refresh.",
                        error_code="OAUTH_ACCOUNT_NOT_FOUND",
                        status_code=404,
                    )

                update_data: Dict[str, Any] = {
                    "access_token_encrypted": new_access_token_encrypted,
                }
                if new_refresh_token_encrypted:
                    update_data["refresh_token_encrypted"] = new_refresh_token_encrypted
                if new_token_expires_at:
                    update_data["token_expires_at"] = new_token_expires_at

                await repo.update(
                    session=self.uow_service.session,
                    id=account.id,
                    obj_in=update_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    OAuthTokenRefreshed(
                        aggregate_id=str(account.id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        oauth_account_id=str(account.id),
                        provider=provider_lower,
                        payload={"user_id": str(user_id), "provider": provider_lower},
                    )
                )

            await self.cache.delete(oauth_account_cache_key(user_id, provider_lower))
            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"refresh_oauth_token failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get or Create User from OAuth (SSO Flow) ─────────────────────────────

    async def get_or_create_user_from_oauth(
        self,
        ctx: ServiceContext,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str],
        full_name: Optional[str],
        access_token_encrypted: Optional[str] = None,
        refresh_token_encrypted: Optional[str] = None,
    ) -> ServiceResult[dict]:
        """
        SSO provisioning flow: find an existing user linked to this provider account,
        or create a new one if none exists.
        Returns dict with 'user' and 'is_new_user' keys.
        """
        try:
            validate_oauth_provider_supported(provider)
            provider_lower = provider.lower()

            async with self.uow_service:
                oauth_repo = _OAuthAccountRepository()

                # Try to find existing linked account
                existing_account = await oauth_repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="provider", operator=FilterOperator.EQ, value=provider_lower),
                        FilterParam(field="provider_user_id", operator=FilterOperator.EQ, value=provider_user_id),
                    ],
                )

                if existing_account:
                    # Update tokens
                    token_update: Dict[str, Any] = {}
                    if access_token_encrypted:
                        token_update["access_token_encrypted"] = access_token_encrypted
                    if refresh_token_encrypted:
                        token_update["refresh_token_encrypted"] = refresh_token_encrypted
                    if token_update:
                        await oauth_repo.update(
                            session=self.uow_service.session,
                            id=existing_account.id,
                            obj_in=token_update,
                        )

                    user_repo = UserRepository()
                    user = await user_repo.get_by_id(
                        session=self.uow_service.session,
                        id=existing_account.user_id,
                    )
                    return ServiceResult.ok(data={"user": user, "is_new_user": False})

                # No existing account — provision new user if email provided
                if not provider_email:
                    return ServiceResult.fail(
                        error="Cannot provision user without an email address from OAuth provider.",
                        error_code="OAUTH_EMAIL_REQUIRED",
                        status_code=422,
                    )

                user_repo = UserRepository()

                # Check if email already exists (account linking scenario)
                existing_user = await user_repo.get_by_email(
                    session=self.uow_service.session,
                    email=provider_email.lower(),
                )

                if existing_user:
                    user = existing_user
                    is_new = False
                else:
                    # Create new user
                    user_data: Dict[str, Any] = {
                        "email": provider_email.lower(),
                        "full_name": full_name or provider_email.split("@")[0],
                        "is_active": True,
                        "is_verified": True,  # OAuth providers verify email
                    }
                    user = await user_repo.create(
                        session=self.uow_service.session,
                        obj_in=user_data,
                    )
                    is_new = True

                # Link the OAuth account to the user
                account_data: Dict[str, Any] = {
                    "user_id": str(user.id),
                    "provider": provider_lower,
                    "provider_user_id": provider_user_id,
                    "access_token_encrypted": access_token_encrypted,
                    "refresh_token_encrypted": refresh_token_encrypted,
                    "provider_email": provider_email,
                    "provider_data": {},
                }
                await oauth_repo.create(
                    session=self.uow_service.session,
                    obj_in=account_data,
                )

                if is_new:
                    self.uow_service.add_event(
                        OAuthUserProvisioned(
                            aggregate_id=str(user.id),
                            tenant_id=ctx.get_org_id_str(),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            new_user_id=str(user.id),
                            provider=provider_lower,
                            provider_email=provider_email,
                            payload={"user_id": str(user.id), "provider": provider_lower},
                        )
                    )

            logger.info(
                "OAuth SSO provisioning complete",
                extra={"provider": provider_lower, "is_new_user": is_new},
            )
            return ServiceResult.ok(data={"user": user, "is_new_user": is_new})

        except Exception as exc:
            logger.error(f"get_or_create_user_from_oauth failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
