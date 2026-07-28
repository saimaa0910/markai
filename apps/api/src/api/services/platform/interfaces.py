"""
EAIMOS Platform Interfaces
===========================
Protocol declarations for Sprint 6 Platform services.
"""

from typing import Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.platform.dtos import (
    AddCreditsDTO,
    AnalyticsQueryDTO,
    AnalyticsSummaryDTO,
    CreateSubscriptionDTO,
    CreditBalanceResponseDTO,
    ReportIncidentDTO,
    SecurityIncidentResponseDTO,
    SubscriptionResponseDTO,
)


class IBillingService(Protocol):
    async def create_subscription(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateSubscriptionDTO
    ) -> ServiceResult[SubscriptionResponseDTO]: ...

    async def add_credits(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: AddCreditsDTO
    ) -> ServiceResult[CreditBalanceResponseDTO]: ...


class IAnalyticsService(Protocol):
    async def query_analytics(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: AnalyticsQueryDTO
    ) -> ServiceResult[AnalyticsSummaryDTO]: ...


class ISecurityPlatformService(Protocol):
    async def report_incident(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: ReportIncidentDTO
    ) -> ServiceResult[SecurityIncidentResponseDTO]: ...
