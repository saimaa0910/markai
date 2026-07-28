"""
EAIMOS Variant Service (Sprint 4)
===================================
Service Layer managing Campaign Content A/B Testing Variants and Analytics.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from api.services.base import ServiceContext, ServiceResult
from api.services.campaign.dtos import CreateVariantDTO, VariantResponseDTO
from api.services.campaign.events import VariantCreated
from api.services.campaign.policies import CampaignPolicy

logger = logging.getLogger("eaimos.campaign.variant")


class VariantService:
    """A/B Testing Variant Service."""

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

    async def create_variant(
        self,
        ctx: ServiceContext,
        dto: CreateVariantDTO,
    ) -> ServiceResult[VariantResponseDTO]:
        try:
            variant_id = uuid.uuid4()
            res_dto = VariantResponseDTO(
                id=variant_id,
                campaign_id=dto.campaign_id,
                variant_name=dto.variant_name,
                content=dto.content,
                subject_line=dto.subject_line,
                click_count=0,
                impression_count=0,
                conversion_count=0,
                created_at=datetime.now(timezone.utc),
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    VariantCreated(
                        aggregate_id=str(dto.campaign_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        campaign_id=str(dto.campaign_id),
                        variant_id=str(variant_id),
                        variant_name=dto.variant_name,
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"create_variant failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
