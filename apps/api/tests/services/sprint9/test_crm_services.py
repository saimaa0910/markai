"""
Sprint 9 CRM & Sales Pipeline Service Tests
=============================================
Tests for PipelineService, DealService, ContactManagementService, and LeadQualificationService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.crm.pipeline_service import PipelineService
from api.services.crm.deal_service import DealService
from api.services.crm.contact_management_service import ContactManagementService
from api.services.crm.lead_qualification_service import LeadQualificationService
from api.services.crm.dtos import (
    CreatePipelineDTO,
    CreateDealDTO,
    CreateLeadDTO,
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


class TestPipelineService:
    @pytest.mark.asyncio
    async def test_create_pipeline(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        p_entity = make_entity(
            organization_id=ctx.organization_id,
            name="Enterprise Sales Pipeline",
            description="B2B Deal Pipeline",
            currency="USD",
            is_default=True,
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = p_entity

        svc = PipelineService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.crm.pipeline_service._PipelineRepository", return_value=repo_mock):
            res = await svc.create_pipeline(
                ctx,
                org_id=ctx.organization_id,
                dto=CreatePipelineDTO(
                    name="Enterprise Sales Pipeline",
                    description="B2B Deal Pipeline",
                    currency="USD",
                    is_default=True,
                ),
            )

        assert res.is_success
        assert res.data.name == "Enterprise Sales Pipeline"


class TestDealService:
    @pytest.mark.asyncio
    async def test_create_deal(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = DealService(authorizer=authorizer)
        res = await svc.create_deal(
            ctx,
            org_id=ctx.organization_id,
            dto=CreateDealDTO(
                pipeline_id=uuid.uuid4(),
                stage_id=uuid.uuid4(),
                title="Acme Corp SaaS Expansion",
                amount=50000.0,
            ),
        )

        assert res.is_success
        assert res.data.title == "Acme Corp SaaS Expansion"
        assert res.data.amount == 50000.0


class TestContactManagementService:
    @pytest.mark.asyncio
    async def test_get_contact_summary(self):
        ctx = make_ctx()

        svc = ContactManagementService()
        contact_id = uuid.uuid4()
        res = await svc.get_contact_summary(ctx, contact_id=contact_id)

        assert res.is_success
        assert res.data["id"] == str(contact_id)


class TestLeadQualificationService:
    @pytest.mark.asyncio
    async def test_create_and_score_lead(self):
        ctx = make_ctx()

        svc = LeadQualificationService()
        res = await svc.create_and_score_lead(
            ctx,
            org_id=ctx.organization_id,
            dto=CreateLeadDTO(
                email="john.smith@globex.com",
                full_name="John Smith",
                company_name="Globex Corp",
            ),
        )

        assert res.is_success
        assert res.data.lead_score == 85
        assert res.data.status == "QUALIFIED"
