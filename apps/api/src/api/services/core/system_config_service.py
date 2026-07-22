"""
EAIMOS System Configuration Service Module (Sprint 1: Core Platform)
======================================================================
Service Layer managing platform settings, configuration key/value pairs, namespaces,
and high-speed read-through caching.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field

from api.models.admin import SystemConfiguration
from api.repositories.filters import FilterParam, FilterOperator
from api.repositories.system_config_repository import SystemConfigRepository
from api.services.base import (
    BaseService,
    ConflictError,
    EnterprisePermission,
    NotFoundError,
    ServiceContext,
    ServiceResult,
    ValidationError,
)


# ── System Configuration DTOs ──────────────────────────────────────────────────

class CreateConfigDTO(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: str
    namespace: str = Field("default", min_length=1, max_length=100)
    data_type: str = Field("string", description="string | number | boolean | json")
    is_encrypted: bool = False
    is_readonly: bool = False
    description: Optional[str] = None
    requires_restart: bool = False
    updated_by: Optional[uuid.UUID] = None


class UpdateConfigDTO(BaseModel):
    value: Optional[str] = None
    data_type: Optional[str] = None
    description: Optional[str] = None
    requires_restart: Optional[bool] = None
    updated_by: Optional[uuid.UUID] = None


class SystemConfigService(BaseService[SystemConfiguration, CreateConfigDTO, UpdateConfigDTO, SystemConfiguration]):
    """
    Enterprise System Configuration Domain Service.
    Coordinates key/value platform parameters with read-through caching.
    """

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
        authorizer: Optional[Any] = None,
    ) -> None:
        super().__init__(
            repository_cls=SystemConfigRepository,
            uow_service=uow_service,
            cache_manager=cache_manager,
            dispatcher=dispatcher,
            authorizer=authorizer,
            entity_name="SystemConfiguration",
            read_permission=EnterprisePermission.IAM_ORG_READ.value,
            write_permission=EnterprisePermission.ADMIN_SYSTEM.value,
        )

    async def before_create(self, ctx: ServiceContext, dto: CreateConfigDTO) -> None:
        """Prevent duplicate configuration key in the same namespace."""
        dto.updated_by = ctx.get_user_id_uuid() or uuid.UUID("00000000-0000-0000-0000-000000000000")
        async with self.uow_service:
            repo = self.uow_service.get_repository(SystemConfigRepository)
            existing = await repo.get_by_key(
                self.uow_service.session, key=dto.key, namespace=dto.namespace
            )
            if existing:
                raise ConflictError(
                    message=f"Config key '{dto.key}' already exists in namespace '{dto.namespace}'.",
                    error_code="CONFIG_KEY_EXISTS",
                )

    async def get_by_key(
        self,
        ctx: ServiceContext,
        key: str,
        namespace: str = "default",
    ) -> ServiceResult[Optional[SystemConfiguration]]:
        """Retrieve system configuration entry by key and namespace with caching."""
        try:
            cache_key = f"sysconfig:{namespace}:{key}"
            cached_val = await self.cache.get(cache_key)
            if cached_val is not None:
                return ServiceResult.ok(data=cached_val, metadata={"cached": True})

            async with self.uow_service:
                repo = self.uow_service.get_repository(SystemConfigRepository)
                cfg = await repo.get_by_key(
                    self.uow_service.session, key=key, namespace=namespace
                )
                if not cfg:
                    return ServiceResult.fail(
                        error=f"Config key '{key}' not found in namespace '{namespace}'.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                return ServiceResult.ok(data=cfg)

        except Exception as exc:
            return ServiceResult.from_exception(exc)
