"""
EAIMOS Campaign Service Interfaces
===================================
Protocol definitions for Sprint 4 Campaign services.
"""

from typing import List, Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.campaign.dtos import (
    CampaignResponseDTO,
    CreateCampaignDTO,
    GenerateContentDTO,
    GeneratedContentResponseDTO,
    UpdateCampaignDTO,
)


class ICampaignService(Protocol):
    async def create_campaign(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateCampaignDTO
    ) -> ServiceResult[CampaignResponseDTO]: ...

    async def get_campaign(
        self, ctx: ServiceContext, campaign_id: Union[uuid.UUID, str]
    ) -> ServiceResult[CampaignResponseDTO]: ...

    async def update_campaign(
        self, ctx: ServiceContext, campaign_id: Union[uuid.UUID, str], dto: UpdateCampaignDTO
    ) -> ServiceResult[CampaignResponseDTO]: ...


class IContentGenerationService(Protocol):
    async def generate_content(
        self, ctx: ServiceContext, dto: GenerateContentDTO
    ) -> ServiceResult[GeneratedContentResponseDTO]: ...
