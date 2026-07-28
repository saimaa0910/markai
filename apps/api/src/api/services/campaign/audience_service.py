"""
EAIMOS Audience Service (Sprint 4)
==================================
Service Layer managing Target Audience Segments and Reach Estimation.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.campaign.cache_keys import audience_segment_cache_key
from api.services.campaign.dtos import AudienceSegmentResponseDTO, CreateAudienceSegmentDTO
from api.services.campaign.events import AudienceSegmentCreated
from api.services.campaign.policies import AudiencePolicy

logger = logging.getLogger("eaimos.campaign.audience")


class AudienceService:
    """Target Audience Segment Service."""

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

    async def create_segment(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateAudienceSegmentDTO,
    ) -> ServiceResult[AudienceSegmentResponseDTO]:
        try:
            AudiencePolicy.can_manage(self.authorizer, ctx, org_id)

            segment_id = uuid.uuid4()
            estimated_reach = 12500  # Mock reach calculation based on filter rules

            res_dto = AudienceSegmentResponseDTO(
                id=segment_id,
                organization_id=uuid.UUID(str(org_id)),
                name=dto.name,
                description=dto.description,
                filters=dto.filters,
                estimated_reach=estimated_reach,
                created_at=datetime.now(timezone.utc),
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    AudienceSegmentCreated(
                        aggregate_id=str(segment_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        segment_id=str(segment_id),
                        name=dto.name,
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"create_segment failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
