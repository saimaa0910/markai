"""
EAIMOS Audit Log Service Module (Sprint 1: Core Platform)
=========================================================
Service Layer recording append-only audit trail logs for security compliance,
administrative actions, and organization security auditing.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field

from api.models.auth import AuditLog
from api.repositories.audit_log_repository import AuditLogRepository
from api.services.base import (
    BaseService,
    EnterprisePermission,
    ServiceContext,
    ServiceResult,
)


# ── Audit Log DTOs ─────────────────────────────────────────────────────────────

class CreateAuditLogDTO(BaseModel):
    action: str = Field(..., min_length=2, max_length=100)
    entity_type: str = Field(..., min_length=2, max_length=100)
    entity_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    actor_id: Optional[uuid.UUID] = None
    actor_email: Optional[str] = None
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None
    description: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    diff: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None


class AuditLogService(BaseService[AuditLog, CreateAuditLogDTO, None, AuditLog]):
    """
    Enterprise Audit Log Domain Service.
    Coordinates append-only compliance logging and organization security queries.
    """

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
        authorizer: Optional[Any] = None,
    ) -> None:
        super().__init__(
            repository_cls=AuditLogRepository,
            uow_service=uow_service,
            cache_manager=cache_manager,
            dispatcher=dispatcher,
            authorizer=authorizer,
            entity_name="AuditLog",
            read_permission=EnterprisePermission.SECURITY_AUDIT_READ.value,
            write_permission=EnterprisePermission.SECURITY_AUDIT_READ.value,
        )

    async def record_audit_log(
        self,
        ctx: ServiceContext,
        action: str,
        entity_type: str,
        entity_id: Optional[Union[uuid.UUID, str]] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[AuditLog]:
        """Record an append-only system audit log entry."""
        try:
            entity_uuid = uuid.UUID(str(entity_id)) if entity_id else None
            org_uuid = uuid.UUID(str(ctx.organization_id)) if ctx.organization_id else None

            dto = CreateAuditLogDTO(
                action=action,
                entity_type=entity_type,
                entity_id=entity_uuid,
                organization_id=org_uuid,
                actor_id=ctx.get_user_id_uuid(),
                actor_ip=ctx.client_ip,
                actor_user_agent=ctx.user_agent,
                description=description,
                diff=details,
                request_id=ctx.correlation_id,
            )
            return await self.create(ctx, dto)
        except Exception as exc:
            return ServiceResult.from_exception(exc)

    async def list_by_organization(
        self,
        ctx: ServiceContext,
        organization_id: Union[uuid.UUID, str],
        limit: int = 50,
        offset: int = 0,
    ) -> ServiceResult[List[AuditLog]]:
        """Query audit log entries for a specific organization."""
        try:
            org_uuid = uuid.UUID(str(organization_id))
            self.authorizer.require_tenant_access(ctx, org_uuid)
            self.authorizer.require_permission(ctx, EnterprisePermission.SECURITY_AUDIT_READ.value)

            async with self.uow_service:
                repo = self.uow_service.get_repository(AuditLogRepository)
                logs = await repo.list_by_organization(
                    self.uow_service.session,
                    organization_id=org_uuid,
                    limit=limit,
                    offset=offset,
                )
                return ServiceResult.ok(data=logs)

        except Exception as exc:
            return ServiceResult.from_exception(exc)
