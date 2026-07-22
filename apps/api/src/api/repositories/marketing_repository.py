"""
EAIMOS Marketing Platform Repository Module — Sprint 8
======================================================
Repository implementations for Marketing Platform models:
Campaign, CampaignTemplate, CampaignAudience, GeneratedContent.
"""

from typing import Any, List, Optional
import uuid

from api.models.campaign import Campaign, CampaignTemplate
from api.models.campaign_audiences import CampaignAudience
from api.models.content_generator import GeneratedContent
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class EnterpriseCampaignRepository(TenantRepository[Campaign]):
    """Data access layer for Marketing Campaigns."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Campaign, organization_id=organization_id)

    async def get_by_name(self, session: Any, name: str) -> Optional[Campaign]:
        filters = [FilterParam(field="name", operator=FilterOperator.EQ, value=name)]
        return await self.find_one(session=session, filters=filters)


class CampaignTemplateRepository(TenantRepository[CampaignTemplate]):
    """Data access layer for Campaign Templates."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(CampaignTemplate, organization_id=organization_id)


class CampaignAudienceRepository(TenantRepository[CampaignAudience]):
    """Data access layer for Campaign Audiences."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(CampaignAudience, organization_id=organization_id)


class GeneratedContentRepository(TenantRepository[GeneratedContent]):
    """Data access layer for AI Generated Marketing Content."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(GeneratedContent, organization_id=organization_id)
