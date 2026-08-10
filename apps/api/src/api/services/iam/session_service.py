"""
EAIMOS IAM Session Service (Sprint 2)
=======================================
Manages the complete lifecycle of authenticated user sessions:
creation with concurrent session enforcement, sliding-window activity refresh,
single/bulk revocation with reason codes, and cache-backed lookup.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from api.models.iam import UserSession
from api.repositories.iam_repository import UserSessionRepository
from api.services.base import (
    BaseService,
    BusinessRuleViolation,
    EnterprisePermission,
    NotFoundError,
    ServiceContext,
    ServiceResult,
    ValidationError,
)
from api.services.iam.cache_keys import (
    SESSION_KEY_TTL,
    invalidate_pattern_for_user_sessions,
    session_cache_key,
    user_sessions_list_key,
)
from api.services.iam.constants import (
    MAX_SESSIONS_PER_USER,
    SESSION_TTL_MINUTES,
)
from api.services.iam.dtos import (
    CreateSessionDTO,
    RevokeSessionDTO,
    SessionListDTO,
    SessionResponseDTO,
    SessionSummaryDTO,
)
from api.services.iam.events import (
    AllSessionsRevoked,
    SessionRevoked,
    UserLoggedIn,
    UserLoggedOut,
)
from api.services.iam.mappers import (
    session_to_response_dto,
    session_to_summary_dto,
    sessions_to_summary_list,
)
from api.services.iam.policies import SessionPolicy
from api.services.iam.validators import (
    validate_max_concurrent_sessions,
    validate_session_not_expired,
    validate_session_not_revoked,
)
# Sprint 8.3.1 Phase 2 - Session Enhancement
from api.services.session_enhancement import enhance_session_metadata

logger = logging.getLogger("eaimos.iam.session")


class SessionService:
    """
    Enterprise IAM Session Domain Service.

    Responsibilities:
    - Create sessions with concurrent session limit enforcement (from SecurityPolicy)
    - Cache-backed session lookups
    - Single/bulk revocation with audit reason tracking
    - Sliding window last_active_at refresh
    """

    ENTITY_NAME = "UserSession"

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

    # ─── Create ───────────────────────────────────────────────────────────────

    async def create_session(
        self,
        ctx: ServiceContext,
        dto: CreateSessionDTO,
    ) -> ServiceResult[SessionResponseDTO]:
        """
        Issue a new authenticated session.

        Business Rules:
        - Enforces SecurityPolicy.max_concurrent_sessions
        - Records device metadata and geolocation for audit
        - Publishes UserLoggedIn domain event
        """
        try:
            SessionPolicy.can_create(self.authorizer, ctx)

            expires_at = datetime.now(timezone.utc) + timedelta(minutes=dto.ttl_minutes)
            last_active_at = datetime.now(timezone.utc)

            async with self.uow_service:
                repo: UserSessionRepository = self.uow_service.get_repository(UserSessionRepository)

                # Enforce concurrent session limit
                active_sessions = await repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=dto.user_id,
                )
                active_non_revoked = [s for s in active_sessions if not s.is_revoked]
                max_sessions = dto.ttl_minutes  # use policy lookup in full integration

                # Default platform ceiling if policy not loaded
                validate_max_concurrent_sessions(
                    active_session_count=len(active_non_revoked),
                    max_allowed=MAX_SESSIONS_PER_USER,
                    user_id=str(dto.user_id),
                )

                session_data: Dict[str, Any] = {
                    "user_id": str(dto.user_id),
                    "organization_id": str(dto.organization_id) if dto.organization_id else None,
                    "ip_address": dto.ip_address,
                    "user_agent": dto.user_agent,
                    "device_fingerprint": dto.device_fingerprint,
                    "country_code": dto.country_code,
                    "city": dto.city,
                    "expires_at": expires_at,
                    "last_active_at": last_active_at,
                    "is_revoked": False,
                }

                session = await repo.create(
                    session=self.uow_service.session,
                    obj_in=session_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                # Sprint 8.3.1 Phase 2: Enhance session with device detection
                enhance_session_metadata(
                    session,
                    user_agent=dto.user_agent,
                    ip_address=dto.ip_address,
                    city=dto.city,
                    country_code=dto.country_code,
                    # Optional: Add region, latitude, longitude if available in dto
                    # region=dto.region if hasattr(dto, 'region') else None,
                    # latitude=dto.latitude if hasattr(dto, 'latitude') else None,
                    # longitude=dto.longitude if hasattr(dto, 'longitude') else None,
                )

                self.uow_service.add_event(
                    UserLoggedIn(
                        aggregate_id=str(session.id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        session_id=str(session.id),
                        ip_address=dto.ip_address,
                        country_code=dto.country_code,
                        user_agent=dto.user_agent,
                        payload={"user_id": str(dto.user_id)},
                    )
                )

            response = session_to_response_dto(session)

            # Cache the new session
            cache_key = session_cache_key(session.id)
            await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=SESSION_KEY_TTL)

            # Invalidate user session list cache
            await self.cache.delete(user_sessions_list_key(dto.user_id))

            logger.info(
                "Session created",
                extra={
                    "session_id": str(session.id),
                    "user_id": str(dto.user_id),
                    "correlation_id": ctx.correlation_id,
                },
            )
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_session failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get ──────────────────────────────────────────────────────────────────

    async def get_session(
        self,
        ctx: ServiceContext,
        session_id: Union[uuid.UUID, str],
    ) -> ServiceResult[SessionResponseDTO]:
        """Retrieve a session record by ID with cache-first lookup."""
        try:
            cache_key = session_cache_key(session_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(
                    data=SessionResponseDTO(**cached),
                    metadata={"cached": True},
                )

            async with self.uow_service:
                repo: UserSessionRepository = self.uow_service.get_repository(UserSessionRepository)
                session = await repo.get_by_id(
                    session=self.uow_service.session,
                    id=session_id,
                )
                if not session:
                    return ServiceResult.fail(
                        error=f"Session '{session_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                SessionPolicy.can_read(self.authorizer, ctx, session.user_id)

                response = session_to_response_dto(session)
                await self.cache.set(
                    cache_key,
                    response.model_dump(mode="json"),
                    ttl=SESSION_KEY_TTL,
                )
                return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_session failed for {session_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── List ─────────────────────────────────────────────────────────────────

    async def list_user_sessions(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        include_revoked: bool = False,
    ) -> ServiceResult[SessionListDTO]:
        """Return all sessions for a user, optionally including revoked ones."""
        try:
            SessionPolicy.can_list(self.authorizer, ctx, target_user_id=user_id)

            if not include_revoked:
                list_cache_key = user_sessions_list_key(user_id)
                cached = await self.cache.get(list_cache_key)
                if cached is not None and isinstance(cached, list):
                    items = [SessionSummaryDTO(**s) for s in cached]
                    return ServiceResult.ok(
                        data=SessionListDTO(items=items, total=len(items), page=1, page_size=len(items)),
                        metadata={"cached": True},
                    )

            async with self.uow_service:
                repo: UserSessionRepository = self.uow_service.get_repository(UserSessionRepository)
                sessions = await repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=uuid.UUID(str(user_id)),
                )

            if not include_revoked:
                sessions = [s for s in sessions if not s.is_revoked]

            summaries = sessions_to_summary_list(sessions)

            if not include_revoked:
                await self.cache.set(
                    user_sessions_list_key(user_id),
                    [s.model_dump(mode="json") for s in summaries],
                    ttl=SESSION_KEY_TTL,
                )

            return ServiceResult.ok(
                data=SessionListDTO(
                    items=summaries,
                    total=len(summaries),
                    page=1,
                    page_size=len(summaries),
                )
            )

        except Exception as exc:
            logger.error(f"list_user_sessions failed for {user_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Revoke Single ────────────────────────────────────────────────────────

    async def revoke_session(
        self,
        ctx: ServiceContext,
        session_id: Union[uuid.UUID, str],
        dto: RevokeSessionDTO,
    ) -> ServiceResult[bool]:
        """Revoke a single session with a documented reason."""
        try:
            async with self.uow_service:
                repo: UserSessionRepository = self.uow_service.get_repository(UserSessionRepository)
                session = await repo.get_by_id(
                    session=self.uow_service.session,
                    id=session_id,
                )
                if not session:
                    return ServiceResult.fail(
                        error=f"Session '{session_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                SessionPolicy.can_revoke(self.authorizer, ctx, session.user_id)
                validate_session_not_revoked(session.is_revoked, str(session_id))

                now = datetime.now(timezone.utc)
                revoke_data = {
                    "is_revoked": True,
                    "revoked_at": now,
                    "revocation_reason": dto.reason or "logout",
                }
                await repo.update(
                    session=self.uow_service.session,
                    id=session_id,
                    obj_in=revoke_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                reason = dto.reason or "logout"
                event_cls = UserLoggedOut if reason == "logout" else SessionRevoked
                event_kwargs: Dict[str, Any] = {
                    "aggregate_id": str(session_id),
                    "tenant_id": ctx.get_org_id_str(),
                    "actor_id": ctx.get_user_id_str(),
                    "correlation_id": ctx.correlation_id,
                    "session_id": str(session_id),
                    "reason": reason,
                    "payload": {"session_id": str(session_id), "reason": reason},
                }
                if event_cls == SessionRevoked:
                    event_kwargs["revoked_by"] = ctx.get_user_id_str()
                self.uow_service.add_event(event_cls(**event_kwargs))

            # Invalidate caches
            await self.cache.delete(session_cache_key(session_id))
            await self.cache.delete(user_sessions_list_key(session.user_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"revoke_session failed for {session_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Revoke All ───────────────────────────────────────────────────────────

    async def revoke_all_user_sessions(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        reason: str = "admin",
    ) -> ServiceResult[int]:
        """Revoke all active sessions for a user (security event or password change)."""
        try:
            SessionPolicy.can_revoke_all(self.authorizer, ctx)

            revoked_count = 0
            async with self.uow_service:
                repo: UserSessionRepository = self.uow_service.get_repository(UserSessionRepository)
                sessions = await repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=uuid.UUID(str(user_id)),
                )
                active = [s for s in sessions if not s.is_revoked]
                revoked_count = len(active)

                now = datetime.now(timezone.utc)
                for s in active:
                    await repo.update(
                        session=self.uow_service.session,
                        id=s.id,
                        obj_in={
                            "is_revoked": True,
                            "revoked_at": now,
                            "revocation_reason": reason,
                        },
                        actor_id=ctx.get_user_id_uuid(),
                    )

                self.uow_service.add_event(
                    AllSessionsRevoked(
                        aggregate_id=str(user_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        user_id=str(user_id),
                        session_count=revoked_count,
                        reason=reason,
                        payload={"user_id": str(user_id), "revoked_count": revoked_count},
                    )
                )

            # Invalidate all session caches for user
            await self.cache.delete_pattern(invalidate_pattern_for_user_sessions(user_id))
            await self.cache.delete(user_sessions_list_key(user_id))

            logger.info(f"Revoked {revoked_count} sessions for user {user_id}, reason: {reason}")
            return ServiceResult.ok(data=revoked_count)

        except Exception as exc:
            logger.error(f"revoke_all_user_sessions failed for {user_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Activity Refresh ─────────────────────────────────────────────────────

    async def refresh_session_activity(
        self,
        ctx: ServiceContext,
        session_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]:
        """Update last_active_at to maintain the sliding session window."""
        try:
            async with self.uow_service:
                repo: UserSessionRepository = self.uow_service.get_repository(UserSessionRepository)
                await repo.update(
                    session=self.uow_service.session,
                    id=session_id,
                    obj_in={"last_active_at": datetime.now(timezone.utc)},
                    actor_id=ctx.get_user_id_uuid(),
                )

            # Invalidate cached session so next read gets fresh last_active_at
            await self.cache.delete(session_cache_key(session_id))
            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.warning(f"refresh_session_activity failed for {session_id}: {exc}")
            return ServiceResult.from_exception(exc)
