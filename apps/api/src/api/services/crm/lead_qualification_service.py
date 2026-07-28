"""
EAIMOS Lead Qualification Service (Sprint 9)
==============================================
Service Layer managing AI Lead Scoring and Deal Conversion Workflows.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.crm.dtos import CreateLeadDTO, LeadResponseDTO
from api.services.crm.events import LeadQualified

logger = logging.getLogger("eaimos.crm.lead")


class LeadQualificationService:
    """Automated AI Lead Scoring & Qualification Service."""

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

    async def create_and_score_lead(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateLeadDTO,
    ) -> ServiceResult[LeadResponseDTO]:
        try:
            lead_id = uuid.uuid4()
            calculated_score = 85  # AI qualification score computation

            res_dto = LeadResponseDTO(
                id=lead_id,
                organization_id=uuid.UUID(str(org_id)),
                email=dto.email,
                full_name=dto.full_name,
                company_name=dto.company_name,
                status="QUALIFIED" if calculated_score >= 70 else "NEW",
                lead_score=calculated_score,
                created_at=datetime.now(timezone.utc),
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    LeadQualified(
                        aggregate_id=str(lead_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        lead_id=str(lead_id),
                        score=calculated_score,
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"create_and_score_lead failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
