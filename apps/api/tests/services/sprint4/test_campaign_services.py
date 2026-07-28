"""
Sprint 4 Campaign & Content Management Service Tests
=====================================================
Tests for CampaignService, AudienceService, ContentGenerationService, and VariantService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.campaign.campaign_service import CampaignService
from api.services.campaign.audience_service import AudienceService
from api.services.campaign.content_generation_service import ContentGenerationService
from api.services.campaign.variant_service import VariantService
from api.services.campaign.dtos import (
    CreateCampaignDTO,
    UpdateCampaignDTO,
    CreateAudienceSegmentDTO,
    GenerateContentDTO,
    CreateVariantDTO,
)


def make_ctx() -> ServiceContext:
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.uuid4()
    ctx.organization_id = uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.is_tenant_member.return_value = True
    return ctx


def make_authorizer() -> MagicMock:
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.return_value = None
    auth.check_permission.return_value = True
    return auth


def make_uow() -> MagicMock:
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = MagicMock()
    uow.add_event = MagicMock()
    return uow


def make_entity(**kwargs) -> MagicMock:
    entity = MagicMock()
    entity.id = kwargs.get("id", uuid.uuid4())
    entity.created_at = datetime.now(timezone.utc)
    for k, v in kwargs.items():
        setattr(entity, k, v)
    return entity


class TestCampaignService:
    @pytest.mark.asyncio
    async def test_create_campaign_success(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        campaign_entity = make_entity(
            organization_id=ctx.organization_id,
            title="Q3 Product Launch",
            description="Email campaign for Q3 product features",
            status="DRAFT",
            channel="EMAIL",
            goal="Conversions",
            budget=5000.0,
            spent_budget=0.0,
            currency="USD",
            scheduled_for=None,
            completed_at=None,
            tags=["q3", "launch"],
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = campaign_entity
        uow.get_repository.return_value = repo_mock

        svc = CampaignService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.campaign.campaign_service._CampaignRepository", return_value=repo_mock):
            res = await svc.create_campaign(
                ctx,
                org_id=ctx.organization_id,
                dto=CreateCampaignDTO(
                    title="Q3 Product Launch",
                    channel="EMAIL",
                    budget=5000.0,
                ),
            )

        assert res.is_success
        assert res.data.title == "Q3 Product Launch"
        assert res.data.channel == "EMAIL"

    @pytest.mark.asyncio
    async def test_update_campaign_status(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        campaign_id = uuid.uuid4()
        campaign_entity = make_entity(
            id=campaign_id,
            organization_id=ctx.organization_id,
            title="Q3 Product Launch",
            status="DRAFT",
            channel="EMAIL",
            budget=5000.0,
            spent_budget=0.0,
            currency="USD",
        )
        updated_entity = make_entity(
            id=campaign_id,
            organization_id=ctx.organization_id,
            title="Q3 Product Launch",
            status="ACTIVE",
            channel="EMAIL",
            budget=5000.0,
            spent_budget=0.0,
            currency="USD",
        )

        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = campaign_entity
        repo_mock.update.return_value = updated_entity
        uow.get_repository.return_value = repo_mock

        svc = CampaignService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.campaign.campaign_service._CampaignRepository", return_value=repo_mock):
            res = await svc.update_campaign(
                ctx,
                campaign_id=campaign_id,
                dto=UpdateCampaignDTO(status="ACTIVE"),
            )

        assert res.is_success
        assert res.data.status == "ACTIVE"


class TestAudienceService:
    @pytest.mark.asyncio
    async def test_create_segment(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = AudienceService(authorizer=authorizer)
        res = await svc.create_segment(
            ctx,
            org_id=ctx.organization_id,
            dto=CreateAudienceSegmentDTO(
                name="High Value Customers",
                filters={"min_spend": 1000},
            ),
        )

        assert res.is_success
        assert res.data.name == "High Value Customers"
        assert res.data.estimated_reach > 0


class TestContentGenerationService:
    @pytest.mark.asyncio
    async def test_generate_content(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = ContentGenerationService(authorizer=authorizer)
        res = await svc.generate_content(
            ctx,
            dto=GenerateContentDTO(
                topic="Summer Sale Discount",
                target_channel="EMAIL",
                tone="urgent",
            ),
        )

        assert res.is_success
        assert "Summer Sale Discount" in res.data.title
        assert len(res.data.variants) == 2


class TestVariantService:
    @pytest.mark.asyncio
    async def test_create_variant(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = VariantService(authorizer=authorizer)
        res = await svc.create_variant(
            ctx,
            dto=CreateVariantDTO(
                campaign_id=uuid.uuid4(),
                variant_name="Variant A",
                content="Get 20% off today!",
                subject_line="Special Discount Inside",
            ),
        )

        assert res.is_success
        assert res.data.variant_name == "Variant A"
