"""
EAIMOS IAM API Key Service (Sprint 2)
=======================================
Manages the full lifecycle of organization API keys:
generation with SHA-256 hashing (plaintext shown once), cache-backed lookup,
IP restriction enforcement, usage tracking, rotation, and soft-delete revocation.
"""

import hashlib
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from api.repositories.iam_repository import APIKeyRepository
from api.services.base import (
    ConflictError,
    EnterprisePermission,
    NotFoundError,
    ServiceContext,
    ServiceResult,
)
from api.services.base.service_exceptions import BusinessRuleViolation
from api.services.iam.cache_keys import (
    API_KEY_KEY_TTL,
    api_key_by_hash_cache_key,
    api_key_by_id_cache_key,
    api_key_list_key,
    invalidate_pattern_for_org_roles,
)
from api.services.iam.constants import (
    API_KEY_MAX_PER_ORG,
    API_KEY_PREFIX_LIVE,
    API_KEY_PREFIX_TEST,
    API_KEY_PREFIX_LENGTH,
)
from api.services.iam.dtos import (
    APIKeyCreatedDTO,
    APIKeyListDTO,
    APIKeyResponseDTO,
    CreateAPIKeyDTO,
    UpdateAPIKeyDTO,
)
from api.services.iam.events import (
    APIKeyCreated,
    APIKeyRevoked,
    APIKeyRotated,
    APIKeyUpdated,
    APIKeyUsed,
)
from api.services.iam.mappers import (
    api_key_to_response_dto,
    api_key_to_summary_dto,
    api_keys_to_summary_list,
)
from api.services.iam.policies import APIKeyPolicy
from api.services.iam.validators import (
    validate_api_key_active,
    validate_api_key_ip_allowlist,
    validate_api_key_limit_not_exceeded,
    validate_api_key_not_expired,
    validate_api_key_scopes,
)

logger = logging.getLogger("eaimos.iam.api_key")


def _generate_raw_key(is_test: bool = False) -> str:
    """Generate a cryptographically secure random API key."""
    prefix = API_KEY_PREFIX_TEST if is_test else API_KEY_PREFIX_LIVE
    token = secrets.token_urlsafe(32)
    return f"{prefix}{token}"


def _hash_key(raw_key: str) -> str:
    """Compute SHA-256 of the raw API key. Only the hash is stored."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _extract_prefix(raw_key: str, prefix_len: int = API_KEY_PREFIX_LENGTH) -> str:
    """Extract the non-secret display prefix from the raw key."""
    return raw_key[:prefix_len]


class APIKeyService:
    """
    Enterprise IAM API Key Domain Service.

    Key security invariant: plaintext keys are NEVER stored.
    The raw key is returned exactly once at creation time.
    All subsequent operations use key_hash for lookup.
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

    # ─── Create ───────────────────────────────────────────────────────────────

    async def create_api_key(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateAPIKeyDTO,
    ) -> ServiceResult[APIKeyCreatedDTO]:
        """
        Generate a new API key for an organization.
        Returns the plaintext key ONCE — it cannot be retrieved after this call.
        """
        try:
            APIKeyPolicy.can_create(self.authorizer, ctx, org_id)
            validate_api_key_scopes(dto.scopes)

            raw_key = _generate_raw_key(is_test=dto.is_test)
            key_hash = _hash_key(raw_key)
            key_prefix = _extract_prefix(raw_key)

            org_uuid = uuid.UUID(str(org_id))
            user_uuid = ctx.get_user_id_uuid()

            async with self.uow_service:
                repo: APIKeyRepository = APIKeyRepository(organization_id=org_uuid)

                # Enforce per-org key limit
                existing_keys = await repo.find_many(session=self.uow_service.session)
                active_keys = [k for k in existing_keys if k.deleted_at is None]
                validate_api_key_limit_not_exceeded(len(active_keys), str(org_id))

                key_data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    "user_id": str(user_uuid),
                    "name": dto.name,
                    "key_prefix": key_prefix,
                    "key_hash": key_hash,
                    "scopes": dto.scopes,
                    "allowed_ips": dto.allowed_ips,
                    "expires_at": dto.expires_at,
                    "is_active": True,
                    "rate_limit_rpm": dto.rate_limit_rpm,
                    "total_calls": 0,
                }

                api_key = await repo.create(
                    session=self.uow_service.session,
                    obj_in=key_data,
                    actor_id=user_uuid,
                )

                self.uow_service.add_event(
                    APIKeyCreated(
                        aggregate_id=str(api_key.id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        api_key_id=str(api_key.id),
                        key_prefix=key_prefix,
                        scopes=dto.scopes,
                        payload={"key_prefix": key_prefix, "org_id": str(org_id)},
                    )
                )

            # Invalidate org key list cache
            await self.cache.delete(api_key_list_key(org_id))

            logger.info(
                "API key created",
                extra={"key_prefix": key_prefix, "org_id": str(org_id), "correlation_id": ctx.correlation_id},
            )
            return ServiceResult.ok(
                data=APIKeyCreatedDTO(
                    id=api_key.id,
                    name=api_key.name,
                    key_prefix=key_prefix,
                    raw_key=raw_key,
                    scopes=dto.scopes,
                    expires_at=dto.expires_at,
                    created_at=api_key.created_at,
                ),
                status_code=201,
            )

        except Exception as exc:
            logger.error(f"create_api_key failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get ──────────────────────────────────────────────────────────────────

    async def get_api_key(
        self,
        ctx: ServiceContext,
        api_key_id: Union[uuid.UUID, str],
    ) -> ServiceResult[APIKeyResponseDTO]:
        """Retrieve a single API key record by ID (no hash/raw key exposed)."""
        try:
            cache_key = api_key_by_id_cache_key(api_key_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(
                    data=APIKeyResponseDTO(**cached),
                    metadata={"cached": True},
                )

            org_uuid = uuid.UUID(str(ctx.organization_id)) if ctx.organization_id else None
            if org_uuid is None:
                return ServiceResult.fail(
                    error="Organization context required to access API keys.",
                    error_code="MISSING_TENANT_CONTEXT",
                    status_code=400,
                )

            async with self.uow_service:
                repo: APIKeyRepository = APIKeyRepository(organization_id=org_uuid)
                api_key = await repo.get_by_id(session=self.uow_service.session, id=api_key_id)
                if not api_key:
                    return ServiceResult.fail(
                        error=f"API key '{api_key_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                APIKeyPolicy.can_read(self.authorizer, ctx, api_key.user_id, api_key.organization_id)

                response = api_key_to_response_dto(api_key)
                await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=API_KEY_KEY_TTL)
                return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_api_key failed for {api_key_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── List ─────────────────────────────────────────────────────────────────

    async def list_api_keys(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        page: int = 1,
        page_size: int = 20,
    ) -> ServiceResult[APIKeyListDTO]:
        """Return paginated API keys for an organization."""
        try:
            APIKeyPolicy.can_list(self.authorizer, ctx, org_id)

            org_uuid = uuid.UUID(str(org_id))
            async with self.uow_service:
                repo: APIKeyRepository = APIKeyRepository(organization_id=org_uuid)
                all_keys = await repo.find_many(session=self.uow_service.session)

            # Non-admins see only their own keys
            if not self.authorizer.check_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value):
                all_keys = [k for k in all_keys if str(k.user_id) == ctx.get_user_id_str()]

            # Pagination
            total = len(all_keys)
            start = (page - 1) * page_size
            paginated = all_keys[start: start + page_size]
            summaries = api_keys_to_summary_list(paginated)

            return ServiceResult.ok(
                data=APIKeyListDTO(
                    items=summaries,
                    total=total,
                    page=page,
                    page_size=page_size,
                )
            )

        except Exception as exc:
            logger.error(f"list_api_keys failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Update ───────────────────────────────────────────────────────────────

    async def update_api_key(
        self,
        ctx: ServiceContext,
        api_key_id: Union[uuid.UUID, str],
        dto: UpdateAPIKeyDTO,
    ) -> ServiceResult[APIKeyResponseDTO]:
        """Update mutable fields of an existing API key."""
        try:
            org_uuid = uuid.UUID(str(ctx.organization_id)) if ctx.organization_id else None
            if org_uuid is None:
                return ServiceResult.fail(
                    error="Organization context required.",
                    error_code="MISSING_TENANT_CONTEXT",
                    status_code=400,
                )

            async with self.uow_service:
                repo: APIKeyRepository = APIKeyRepository(organization_id=org_uuid)
                api_key = await repo.get_by_id(session=self.uow_service.session, id=api_key_id)
                if not api_key:
                    return ServiceResult.fail(
                        error=f"API key '{api_key_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                APIKeyPolicy.can_update(self.authorizer, ctx, api_key.user_id, api_key.organization_id)

                if dto.scopes is not None:
                    validate_api_key_scopes(dto.scopes)

                update_data = dto.model_dump(exclude_unset=True)
                changes = {k: str(v) for k, v in update_data.items()}

                updated = await repo.update(
                    session=self.uow_service.session,
                    id=api_key_id,
                    obj_in=update_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    APIKeyUpdated(
                        aggregate_id=str(api_key_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        api_key_id=str(api_key_id),
                        changes=changes,
                        payload={"api_key_id": str(api_key_id), "changes": changes},
                    )
                )

            await self.cache.delete(api_key_by_id_cache_key(api_key_id))
            await self.cache.delete(api_key_list_key(org_uuid))

            response = api_key_to_response_dto(updated)
            return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error("update_api_key failed", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Revoke ───────────────────────────────────────────────────────────────

    async def revoke_api_key(
        self,
        ctx: ServiceContext,
        api_key_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]:
        """Soft-delete (revoke) an API key. It can no longer authenticate requests."""
        try:
            org_uuid = uuid.UUID(str(ctx.organization_id)) if ctx.organization_id else None
            if org_uuid is None:
                return ServiceResult.fail(
                    error="Organization context required.",
                    error_code="MISSING_TENANT_CONTEXT",
                    status_code=400,
                )

            async with self.uow_service:
                repo: APIKeyRepository = APIKeyRepository(organization_id=org_uuid)
                api_key = await repo.get_by_id(session=self.uow_service.session, id=api_key_id)
                if not api_key:
                    return ServiceResult.fail(
                        error=f"API key '{api_key_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                APIKeyPolicy.can_revoke(self.authorizer, ctx, api_key.user_id, api_key.organization_id)

                await repo.soft_delete(
                    session=self.uow_service.session,
                    id=api_key_id,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    APIKeyRevoked(
                        aggregate_id=str(api_key_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        api_key_id=str(api_key_id),
                        key_prefix=api_key.key_prefix,
                        payload={"api_key_id": str(api_key_id)},
                    )
                )

            await self.cache.delete(api_key_by_id_cache_key(api_key_id))
            await self.cache.delete(api_key_list_key(org_uuid))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"revoke_api_key failed for {api_key_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Validate (Authentication Path) ──────────────────────────────────────

    async def validate_api_key(
        self,
        raw_key: str,
        ip_address: Optional[str] = None,
    ) -> ServiceResult[APIKeyResponseDTO]:
        """
        Authenticate a raw API key by computing its hash and looking up the record.
        Enforces IP allowlist, expiry, and active status.
        This method does NOT require a ServiceContext (called from auth middleware).
        """
        try:
            key_hash = _hash_key(raw_key)

            cache_key = api_key_by_hash_cache_key(key_hash)
            cached = await self.cache.get(cache_key)

            if cached is not None:
                api_key_dto = APIKeyResponseDTO(**cached)
                validate_api_key_active(api_key_dto.is_active, api_key_dto.key_prefix)
                validate_api_key_not_expired(api_key_dto.expires_at, api_key_dto.key_prefix)
                if ip_address and api_key_dto.allowed_ips:
                    validate_api_key_ip_allowlist(ip_address, api_key_dto.allowed_ips)
                return ServiceResult.ok(data=api_key_dto, metadata={"cached": True})

            # Must find the org context from the key itself — use a cross-tenant search
            # (base repo search by key_hash without tenant filter for auth path)
            from api.repositories.base import BaseRepository
            from api.models.iam import APIKey
            from api.repositories.filters import FilterParam, FilterOperator

            class _GlobalAPIKeyRepo(BaseRepository[APIKey]):
                def __init__(self) -> None:
                    super().__init__(APIKey)

            system_ctx = ServiceContext.create_system_context()
            async with self.uow_service:
                global_repo = _GlobalAPIKeyRepo()
                filters = [FilterParam(field="key_hash", operator=FilterOperator.EQ, value=key_hash)]
                api_key = await global_repo.find_one(
                    session=self.uow_service.session,
                    filters=filters,
                )

            if not api_key:
                return ServiceResult.fail(
                    error="Invalid API key.",
                    error_code="API_KEY_INVALID",
                    status_code=401,
                )

            validate_api_key_active(api_key.is_active, api_key.key_prefix)
            validate_api_key_not_expired(api_key.expires_at, api_key.key_prefix)
            if ip_address:
                validate_api_key_ip_allowlist(ip_address, api_key.allowed_ips)

            response = api_key_to_response_dto(api_key)
            await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=API_KEY_KEY_TTL)
            return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.warning(f"API key validation failed: {exc}")
            return ServiceResult.from_exception(exc)

    # ─── Record Usage ─────────────────────────────────────────────────────────

    async def record_api_key_usage(
        self,
        api_key_id: Union[uuid.UUID, str],
        ip_address: Optional[str] = None,
    ) -> ServiceResult[bool]:
        """Increment total_calls and update last_used_at for usage tracking."""
        try:
            system_ctx = ServiceContext.create_system_context()
            async with self.uow_service:
                from api.repositories.base import BaseRepository
                from api.models.iam import APIKey

                class _GlobalAPIKeyRepo(BaseRepository[APIKey]):
                    def __init__(self) -> None:
                        super().__init__(APIKey)

                repo = _GlobalAPIKeyRepo()
                api_key = await repo.get_by_id(session=self.uow_service.session, id=api_key_id)
                if api_key:
                    await repo.update(
                        session=self.uow_service.session,
                        id=api_key_id,
                        obj_in={
                            "last_used_at": datetime.now(timezone.utc),
                            "last_used_ip": ip_address,
                            "total_calls": (api_key.total_calls or 0) + 1,
                        },
                    )

            await self.cache.delete(api_key_by_id_cache_key(api_key_id))
            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.warning(f"record_api_key_usage failed for {api_key_id}: {exc}")
            return ServiceResult.from_exception(exc)
