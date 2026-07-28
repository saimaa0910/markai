"""
EAIMOS Campaign Service Layer (Sprint 4)
=========================================
Public API for Content & Campaign Management domain services.
"""

from api.services.campaign.campaign_service import CampaignService
from api.services.campaign.audience_service import AudienceService
from api.services.campaign.content_generation_service import ContentGenerationService
from api.services.campaign.variant_service import VariantService

from api.services.campaign.dtos import (
    CreateCampaignDTO,
    UpdateCampaignDTO,
    CampaignResponseDTO,
    CreateAudienceSegmentDTO,
    AudienceSegmentResponseDTO,
    GenerateContentDTO,
    GeneratedContentResponseDTO,
    CreateVariantDTO,
    VariantResponseDTO,
)

from api.services.campaign.events import (
    CampaignCreated,
    CampaignStatusChanged,
    CampaignScheduled,
    AudienceSegmentCreated,
    ContentGenerated,
    VariantCreated,
)

from api.services.campaign.dependencies import (
    get_campaign_service,
    get_audience_service,
    get_content_generation_service,
    get_variant_service,
)

__all__ = [
    "CampaignService",
    "AudienceService",
    "ContentGenerationService",
    "VariantService",
    "CreateCampaignDTO",
    "UpdateCampaignDTO",
    "CampaignResponseDTO",
    "CreateAudienceSegmentDTO",
    "AudienceSegmentResponseDTO",
    "GenerateContentDTO",
    "GeneratedContentResponseDTO",
    "CreateVariantDTO",
    "VariantResponseDTO",
    "get_campaign_service",
    "get_audience_service",
    "get_content_generation_service",
    "get_variant_service",
]
