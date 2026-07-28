"""
EAIMOS Content Generation Service (Sprint 4)
==============================================
Service Layer for AI-driven Marketing Content Generation and Copywriting.
"""

import logging
from typing import Any, Optional
from api.services.base import ServiceContext, ServiceResult
from api.services.campaign.dtos import GenerateContentDTO, GeneratedContentResponseDTO
from api.services.campaign.events import ContentGenerated
from api.services.campaign.policies import ContentGenPolicy

logger = logging.getLogger("eaimos.campaign.content_gen")


class ContentGenerationService:
    """AI Marketing Copy Generation Service."""

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

    async def generate_content(
        self,
        ctx: ServiceContext,
        dto: GenerateContentDTO,
    ) -> ServiceResult[GeneratedContentResponseDTO]:
        try:
            ContentGenPolicy.can_generate(self.authorizer, ctx)

            res_dto = GeneratedContentResponseDTO(
                title=f"AI Generated Copy: {dto.topic}",
                primary_content=f"Discover the power of {dto.topic}. Designed for high performance and scalability in tone: {dto.tone}.",
                variants=[
                    f"Option A: Transform your workflow with {dto.topic}.",
                    f"Option B: Supercharge your team using {dto.topic}.",
                ],
                suggested_subject_lines=[
                    f"Unlock {dto.topic} today!",
                    f"Exclusive Insights on {dto.topic}",
                ],
                estimated_read_time_min=1.5,
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    ContentGenerated(
                        aggregate_id=str(dto.campaign_id) if dto.campaign_id else "independent",
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        campaign_id=str(dto.campaign_id) if dto.campaign_id else None,
                        target_channel=dto.target_channel,
                    )
                )

            return ServiceResult.ok(data=res_dto)

        except Exception as exc:
            logger.error(f"generate_content failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
