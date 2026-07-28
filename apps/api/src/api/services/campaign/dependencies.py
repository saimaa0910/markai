"""
EAIMOS Campaign Dependencies
==============================
FastAPI dependency injection providers for Sprint 4 Campaign services.
"""

from api.services.base.dependency_provider import container
from api.services.campaign.campaign_service import CampaignService
from api.services.campaign.audience_service import AudienceService
from api.services.campaign.content_generation_service import ContentGenerationService
from api.services.campaign.variant_service import VariantService


def get_campaign_service() -> CampaignService:
    return CampaignService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_audience_service() -> AudienceService:
    return AudienceService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_content_generation_service() -> ContentGenerationService:
    return ContentGenerationService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_variant_service() -> VariantService:
    return VariantService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
