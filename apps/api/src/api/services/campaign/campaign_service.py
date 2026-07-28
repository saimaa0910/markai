"""
EAIMOS Campaign Service (Sprint 4)
===================================
Service Layer managing Campaign Creation, Status Transitions, Scheduling, and Budgets.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from api.models.campaign import Campaign, CampaignChannel, CampaignStatus
from api.repositories.base import BaseRepository
from api.services.base import ServiceContext, ServiceResult
from api.services.campaign.cache_keys import (
    CAMPAIGN_CACHE_TTL,
    campaign_cache_key,
    org_campaigns_list_key,
)
from api.services.campaign.dtos import (
    CampaignResponseDTO,
    CreateCampaignDTO,
    UpdateCampaignDTO,
)
from api.services.campaign.events import (
    CampaignCreated,
    CampaignScheduled,
    CampaignStatusChanged,
)
from api.services.campaign.mappers import campaign_to_response_dto
from api.services.campaign.policies import CampaignPolicy
from api.services.campaign.validators import (
    validate_campaign_status_supported,
    validate_channel_supported,
    validate_schedule_time_future,
)

logger = logging.getLogger("eaimos.campaign.service")


class _CampaignRepository(BaseRepository[Campaign]):
    def __init__(self) -> None:
        super().__init__(Campaign)


class CampaignService:
    """Enterprise Campaign Management Service."""

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

    async def create_campaign(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateCampaignDTO,
    ) -> ServiceResult[CampaignResponseDTO]:
        try:
            CampaignPolicy.can_create(self.authorizer, ctx, org_id)
            validate_channel_supported(dto.channel)

            if dto.scheduled_for:
                validate_schedule_time_future(dto.scheduled_for)

            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                repo = _CampaignRepository()
                campaign_data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    "owner_id": ctx.get_user_id_str(),
                    "title": dto.title,
                    "description": dto.description,
                    "status": CampaignStatus.SCHEDULED if dto.scheduled_for else CampaignStatus.DRAFT,
                    "channel": CampaignChannel(dto.channel.upper()),
                    "goal": dto.goal,
                    "budget": dto.budget,
                    "spent_budget": 0.0,
                    "currency": dto.currency.upper(),
                    "target_audience_id": str(dto.target_audience_id) if dto.target_audience_id else None,
                    "scheduled_for": dto.scheduled_for,
                    "tags": dto.tags,
                }

                campaign = await repo.create(
                    session=self.uow_service.session,
                    obj_in=campaign_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        CampaignCreated(
                            aggregate_id=str(campaign.id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            campaign_id=str(campaign.id),
                            title=dto.title,
                            channel=dto.channel,
                        )
                    )

            await self.cache.delete(org_campaigns_list_key(org_id))
            response = campaign_to_response_dto(campaign)
            await self.cache.set(campaign_cache_key(campaign.id), response.model_dump(mode="json"), ttl=CAMPAIGN_CACHE_TTL)
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_campaign failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def get_campaign(
        self,
        ctx: ServiceContext,
        campaign_id: Union[uuid.UUID, str],
    ) -> ServiceResult[CampaignResponseDTO]:
        try:
            cache_key = campaign_cache_key(campaign_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(data=CampaignResponseDTO(**cached), metadata={"cached": True})

            async with self.uow_service:
                repo = _CampaignRepository()
                campaign = await repo.get_by_id(session=self.uow_service.session, id=campaign_id)
                if not campaign:
                    return ServiceResult.fail(error=f"Campaign '{campaign_id}' not found.", error_code="NOT_FOUND", status_code=404)

                CampaignPolicy.can_read(self.authorizer, ctx, org_id=campaign.organization_id)

                response = campaign_to_response_dto(campaign)
                await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=CAMPAIGN_CACHE_TTL)
                return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_campaign failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def update_campaign(
        self,
        ctx: ServiceContext,
        campaign_id: Union[uuid.UUID, str],
        dto: UpdateCampaignDTO,
    ) -> ServiceResult[CampaignResponseDTO]:
        try:
            async with self.uow_service:
                repo = _CampaignRepository()
                campaign = await repo.get_by_id(session=self.uow_service.session, id=campaign_id)
                if not campaign:
                    return ServiceResult.fail(error=f"Campaign '{campaign_id}' not found.", error_code="NOT_FOUND", status_code=404)

                CampaignPolicy.can_update(self.authorizer, ctx, org_id=campaign.organization_id)

                update_data = dto.model_dump(exclude_unset=True)
                if "status" in update_data and update_data["status"]:
                    validate_campaign_status_supported(update_data["status"])
                    update_data["status"] = CampaignStatus(update_data["status"].upper())

                updated = await repo.update(
                    session=self.uow_service.session,
                    id=campaign_id,
                    obj_in=update_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

            await self.cache.delete(campaign_cache_key(campaign_id))
            return ServiceResult.ok(data=campaign_to_response_dto(updated))

        except Exception as exc:
            logger.error(f"update_campaign failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
