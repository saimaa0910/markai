"""
EAIMOS Billing Repository Module — Sprint 12
============================================
Repository implementations for Billing models:
BillingPlan, Subscription, Invoice, Payment, Credit, UsageRecord.
"""

from typing import Any, List, Optional
import uuid

from api.models.billing import (
    BillingPlan,
    Subscription,
    Invoice,
    Payment,
    Credit,
    UsageRecord,
)
from api.repositories.tenant import TenantRepository
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, FilterOperator


class BillingPlanRepository(BaseRepository[BillingPlan]):
    """Data access layer for Billing Plans."""

    def __init__(self) -> None:
        super().__init__(BillingPlan)

    async def get_by_code(self, session: Any, code: str) -> Optional[BillingPlan]:
        filters = [FilterParam(field="code", operator=FilterOperator.EQ, value=code)]
        return await self.find_one(session=session, filters=filters)


class SubscriptionRepository(TenantRepository[Subscription]):
    """Data access layer for Tenant Subscriptions."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Subscription, organization_id=organization_id)

    async def get_active_subscription(self, session: Any) -> Optional[Subscription]:
        filters = [FilterParam(field="status", operator=FilterOperator.EQ, value="active")]
        return await self.find_one(session=session, filters=filters)


class InvoiceRepository(TenantRepository[Invoice]):
    """Data access layer for Customer Invoices."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Invoice, organization_id=organization_id)


class PaymentRepository(TenantRepository[Payment]):
    """Data access layer for Payment Records."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Payment, organization_id=organization_id)


class CreditRepository(TenantRepository[Credit]):
    """Data access layer for AI Credits Balance."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Credit, organization_id=organization_id)


class UsageRecordRepository(TenantRepository[UsageRecord]):
    """Data access layer for Metered Usage Records."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(UsageRecord, organization_id=organization_id)
