"""
EAIMOS Security Platform Service (Sprint 6)
============================================
Service Layer managing Threat Detection, Security Incident Reporting, and Compliance.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.platform.dtos import ReportIncidentDTO, SecurityIncidentResponseDTO
from api.services.platform.events import SecurityIncidentReported
from api.services.platform.policies import SecurityPlatformPolicy
from api.services.platform.validators import validate_threat_severity_supported

logger = logging.getLogger("eaimos.platform.security")


class SecurityPlatformService:
    """Security Incident Monitoring & Compliance Service."""

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

    async def report_incident(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: ReportIncidentDTO,
    ) -> ServiceResult[SecurityIncidentResponseDTO]:
        try:
            SecurityPlatformPolicy.can_manage(self.authorizer, ctx, org_id)
            validate_threat_severity_supported(dto.severity)

            incident_id = uuid.uuid4()
            now = datetime.now(timezone.utc)

            res_dto = SecurityIncidentResponseDTO(
                id=incident_id,
                organization_id=uuid.UUID(str(org_id)),
                title=dto.title,
                severity=dto.severity.upper(),
                status="OPEN",
                description=dto.description,
                reported_at=now,
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    SecurityIncidentReported(
                        aggregate_id=str(incident_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        incident_id=str(incident_id),
                        severity=dto.severity.upper(),
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"report_incident failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
