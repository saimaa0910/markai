"""
EAIMOS Incident Alert Service (Sprint 11)
===========================================
Service Layer managing System Incidents & Multi-Channel Alert Routing.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.observability.dtos import CreateIncidentDTO, IncidentResponseDTO
from api.services.observability.events import IncidentCreated
from api.services.observability.validators import validate_alert_severity_supported

logger = logging.getLogger("eaimos.observability.incident")


class IncidentAlertService:
    """Incident Detection & Alert Routing Service."""

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

    async def create_incident(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateIncidentDTO,
    ) -> ServiceResult[IncidentResponseDTO]:
        try:
            validate_alert_severity_supported(dto.severity)
            inc_id = uuid.uuid4()
            now = datetime.now(timezone.utc)

            res_dto = IncidentResponseDTO(
                id=inc_id,
                component=dto.component,
                service=dto.service,
                severity=dto.severity.upper(),
                status="active",
                root_cause=dto.root_cause,
                start_time=now,
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    IncidentCreated(
                        aggregate_id=str(inc_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        incident_id=str(inc_id),
                        severity=dto.severity.upper(),
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"create_incident failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
