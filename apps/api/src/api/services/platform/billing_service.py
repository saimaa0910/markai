"""
EAIMOS Billing Service (Sprint 6)
==================================
Service Layer managing SaaS Subscriptions, Plan Tiers, and Append-Only Credit Ledger.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.platform.cache_keys import org_credits_cache_key, org_subscription_cache_key
from api.services.platform.dtos import (
    AddCreditsDTO,
    CreateSubscriptionDTO,
    CreditBalanceResponseDTO,
    SubscriptionResponseDTO,
)
from api.services.platform.events import CreditsAdded, SubscriptionCreated
from api.services.platform.policies import BillingPolicy
from api.services.platform.validators import validate_plan_tier_supported

logger = logging.getLogger("eaimos.platform.billing")


class BillingService:
    """SaaS Billing, Subscriptions & Credit Ledger Service."""

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

    async def create_subscription(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateSubscriptionDTO,
    ) -> ServiceResult[SubscriptionResponseDTO]:
        try:
            BillingPolicy.can_manage(self.authorizer, ctx, org_id)
            validate_plan_tier_supported(dto.plan_tier)

            sub_id = uuid.uuid4()
            now = datetime.now(timezone.utc)
            period_end = now + timedelta(days=365 if dto.billing_cycle.upper() == "ANNUAL" else 30)

            res_dto = SubscriptionResponseDTO(
                id=sub_id,
                organization_id=uuid.UUID(str(org_id)),
                plan_tier=dto.plan_tier.upper(),
                billing_cycle=dto.billing_cycle.upper(),
                status="ACTIVE",
                current_period_start=now,
                current_period_end=period_end,
                cancel_at_period_end=False,
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    SubscriptionCreated(
                        aggregate_id=str(sub_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        subscription_id=str(sub_id),
                        plan_tier=dto.plan_tier.upper(),
                    )
                )

            await self.cache.delete(org_subscription_cache_key(org_id))
            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"create_subscription failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def add_credits(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: AddCreditsDTO,
    ) -> ServiceResult[CreditBalanceResponseDTO]:
        try:
            BillingPolicy.can_manage(self.authorizer, ctx, org_id)

            # Append-only credit ledger transaction
            cache_key = org_credits_cache_key(org_id)
            current_bal = await self.cache.get(cache_key) or 0.0
            new_bal = float(current_bal) + dto.amount

            await self.cache.set(cache_key, new_bal)

            if self.dispatcher:
                await self.dispatcher.publish(
                    CreditsAdded(
                        aggregate_id=str(org_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        amount=dto.amount,
                    )
                )

            res_dto = CreditBalanceResponseDTO(
                organization_id=uuid.UUID(str(org_id)),
                balance=new_bal,
                currency="USD",
            )
            return ServiceResult.ok(data=res_dto)

        except Exception as exc:
            logger.error(f"add_credits failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
