"""
EAIMOS Deal Service (Sprint 9)
===============================
Service Layer managing Deals, Revenue Opportunities, and Stage Progression.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.crm.dtos import CreateDealDTO, DealResponseDTO
from api.services.crm.events import DealCreated
from api.services.crm.policies import CRMPolicy

logger = logging.getLogger("eaimos.crm.deal")


class DealService:
    """Sales Opportunity & Revenue Deal Service."""

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

    async def create_deal(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateDealDTO,
    ) -> ServiceResult[DealResponseDTO]:
        try:
            CRMPolicy.can_manage_deals(self.authorizer, ctx, org_id)
            deal_id = uuid.uuid4()

            res_dto = DealResponseDTO(
                id=deal_id,
                organization_id=uuid.UUID(str(org_id)),
                pipeline_id=dto.pipeline_id,
                stage_id=dto.stage_id,
                title=dto.title,
                amount=dto.amount,
                status="OPEN",
                created_at=datetime.now(timezone.utc),
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    DealCreated(
                        aggregate_id=str(deal_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        deal_id=str(deal_id),
                        amount=dto.amount,
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"create_deal failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
