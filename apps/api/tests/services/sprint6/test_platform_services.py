"""
Sprint 6 Billing, Analytics & Security Platform Service Tests
===============================================================
Tests for BillingService, AnalyticsService, and SecurityPlatformService.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.platform.billing_service import BillingService
from api.services.platform.analytics_service import AnalyticsService
from api.services.platform.security_platform_service import SecurityPlatformService
from api.services.platform.dtos import (
    CreateSubscriptionDTO,
    AddCreditsDTO,
    AnalyticsQueryDTO,
    ReportIncidentDTO,
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


class TestBillingService:
    @pytest.mark.asyncio
    async def test_create_subscription(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()

        svc = BillingService(cache_manager=cache, authorizer=authorizer)
        res = await svc.create_subscription(
            ctx,
            org_id=ctx.organization_id,
            dto=CreateSubscriptionDTO(
                plan_tier="STARTER",
                billing_cycle="MONTHLY",
            ),
        )

        assert res.is_success
        assert res.data.plan_tier == "STARTER"

    @pytest.mark.asyncio
    async def test_add_credits(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()

        svc = BillingService(cache_manager=cache, authorizer=authorizer)
        res = await svc.add_credits(
            ctx,
            org_id=ctx.organization_id,
            dto=AddCreditsDTO(amount=150.0, description="Monthly bonus credits"),
        )

        assert res.is_success
        assert res.data.balance == 150.0


class TestAnalyticsService:
    @pytest.mark.asyncio
    async def test_query_analytics(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = AnalyticsService(authorizer=authorizer)
        now = datetime.now(timezone.utc)
        res = await svc.query_analytics(
            ctx,
            org_id=ctx.organization_id,
            dto=AnalyticsQueryDTO(
                metric="ai_requests_count",
                period="DAY",
                start_date=now - timedelta(days=7),
                end_date=now,
            ),
        )

        assert res.is_success
        assert res.data.metric == "ai_requests_count"
        assert res.data.total_value > 0.0


class TestSecurityPlatformService:
    @pytest.mark.asyncio
    async def test_report_incident(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = SecurityPlatformService(authorizer=authorizer)
        res = await svc.report_incident(
            ctx,
            org_id=ctx.organization_id,
            dto=ReportIncidentDTO(
                title="Suspicious Login Detected",
                severity="HIGH",
                description="Multiple failed login attempts from unknown IP.",
            ),
        )

        assert res.is_success
        assert res.data.title == "Suspicious Login Detected"
        assert res.data.severity == "HIGH"
