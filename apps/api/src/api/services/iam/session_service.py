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

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

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


# ─── Sync/Async Session Helpers ───────────────────────────────────────────────

async def _session_execute(db, stmt):
    """Execute a statement against either an async or sync session."""
    if isinstance(db, AsyncSession):
        return await db.execute(stmt)
    return db.execute(stmt)


async def _session_commit(db):
    """Commit against either an async or sync session."""
    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()


async def _session_refresh(db, obj):
    """Refresh an object against either an async or sync session."""
    if isinstance(db, AsyncSession):
        await db.refresh(obj)
    else:
        db.refresh(obj)


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
        """Issue a new authenticated session.

        Business rules (instance interface, matches ISessionService):
        - Enforces SecurityPolicy.max_concurrent_sessions
        - Records device metadata and geolocation for audit
        - Caches the new session and publishes UserLoggedIn domain event
        """
        try:
            SessionPolicy.can_create(self.authorizer, ctx)

            expires_at = datetime.now(timezone.utc) + timedelta(minutes=dto.ttl_minutes)
            last_active_at = datetime.now(timezone.utc)

            async with self.uow_service:
                repo: UserSessionRepository = self.uow_service.get_repository(UserSessionRepository)

                active_sessions = await repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=dto.user_id,
                )
                active_non_revoked = [s for s in active_sessions if not s.is_revoked]

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

                enhance_session_metadata(
                    session,
                    user_agent=dto.user_agent,
                    ip_address=dto.ip_address,
                    city=dto.city,
                    country_code=dto.country_code,
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

            cache_key = session_cache_key(session.id)
            await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=SESSION_KEY_TTL)
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

    @staticmethod
    async def create_session_row(
        db,
        user_id,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new authenticated session row (DB convenience helper).

        Accepts either an async ``AsyncSession`` or a sync ``Session``.
        Returns a plain dict (user_id, ip_address, user_agent, session_token).
        """
        device_info = device_info or {}
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=SESSION_TTL_MINUTES)
        session = UserSession(
            user_id=user_id,
            session_token=str(uuid.uuid4()),
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_info.get("name") or device_info.get("device_name"),
            device_type=device_info.get("type") or device_info.get("device_type"),
            browser=device_info.get("browser"),
            os=device_info.get("os"),
            expires_at=expires_at,
            last_active_at=datetime.now(timezone.utc),
        )
        db.add(session)
        await _session_commit(db)
        await _session_refresh(db, session)
        return {
            "user_id": str(session.user_id),
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "session_token": str(session.id),
            "id": str(session.id),
        }

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

    # ─── List (test-facing) ───────────────────────────────────────────────────

    @staticmethod
    async def get_user_sessions(
        db,
        user_id,
        include_revoked: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return all sessions for a user as plain dicts."""
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        if not include_revoked:
            stmt = stmt.where(UserSession.is_revoked == False)
        stmt = stmt.order_by(UserSession.last_active_at.desc())
        result = await _session_execute(db, stmt)
        sessions = result.scalars().all()
        return [
            {
                "id": str(s.id),
                "user_id": str(s.user_id),
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "device_name": s.device_name,
                "device_type": s.device_type,
                "created_at": s.created_at,
                "last_activity_at": s.last_active_at,
                "expires_at": s.expires_at,
                "is_active": not s.is_revoked,
                "is_revoked": s.is_revoked,
            }
            for s in sessions
        ]

    # ─── Revoke Single (interface) ────────────────────────────────────────────

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

            await self.cache.delete(session_cache_key(session_id))
            await self.cache.delete(user_sessions_list_key(session.user_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"revoke_session failed for {session_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    @staticmethod
    async def revoke_session_row(
        db,
        session_id,
        user_id=None,
        reason: str = "logout",
    ) -> None:
        """Revoke a single session row with a documented reason (DB helper)."""
        stmt = select(UserSession).where(UserSession.id == session_id)
        if user_id is not None:
            stmt = stmt.where(UserSession.user_id == user_id)
        result = await _session_execute(db, stmt)
        session = result.scalars().first()
        if session is None:
            return
        session.is_revoked = True
        session.revoked_at = datetime.now(timezone.utc)
        session.revocation_reason = reason
        await _session_commit(db)

    # ─── Revoke All (test-facing) ─────────────────────────────────────────────

    @staticmethod
    async def revoke_all_sessions(db, user_id) -> int:
        """Revoke all active sessions for a user; returns the revoked count."""
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_revoked == False)
            .values(
                is_revoked=True,
                revoked_at=datetime.now(timezone.utc),
                revocation_reason="logout_all_devices",
            )
            .execution_options(synchronize_session=False)
        )
        result = await _session_execute(db, stmt)
        await _session_commit(db)
        return result.rowcount

    # ─── Cleanup ──────────────────────────────────────────────────────────────

    @staticmethod
    async def cleanup_expired_sessions(db) -> int:
        """Delete expired sessions; returns the number of rows deleted."""
        now = datetime.now(timezone.utc)
        stmt = delete(UserSession).where(UserSession.expires_at < now)
        result = await _session_execute(db, stmt)
        await _session_commit(db)
        return result.rowcount

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
