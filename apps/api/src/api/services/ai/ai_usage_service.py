"""
EAIMOS AI Usage Service (Sprint 3)
===================================
Service Layer for Tracking Token Consumption, Calculating USD Costs, and Quota Auditing.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.ai.constants import MODEL_PRICING_PER_1K
from api.services.ai.dtos import RecordUsageDTO, UsageSummaryDTO
from api.services.ai.events import AIUsageRecorded
from api.services.ai.policies import AIUsagePolicy

logger = logging.getLogger("eaimos.ai.usage")


class AIUsageService:
    """Token Metering & AI Cost Analytics Service."""

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

    async def record_usage(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: RecordUsageDTO,
    ) -> ServiceResult[bool]:
        try:
            org_uuid = uuid.UUID(str(org_id))
            pricing = MODEL_PRICING_PER_1K.get(dto.model, {"input": 0.0025, "output": 0.01})
            cost_in = (dto.prompt_tokens / 1000.0) * pricing["input"]
            cost_out = (dto.completion_tokens / 1000.0) * pricing["output"]
            total_cost = round(cost_in + cost_out, 6)

            total_tokens = dto.prompt_tokens + dto.completion_tokens

            async with self.uow_service:
                from api.repositories.ai_gateway_repository import AITokenUsageRepository
                from decimal import Decimal
                repo = AITokenUsageRepository(organization_id=org_uuid)
                
                # Check status
                status_val = dto.status if hasattr(dto, "status") else "success"

                # Idempotency (P2-4): dedupe on request-level key when provided
                if getattr(dto, "request_id", None):
                    existing = await repo.find_by_request_id(
                        session=self.uow_service.session, request_id=dto.request_id, status=status_val
                    )
                    if existing:
                        return ServiceResult.ok(data=True, status_code=200)

                await repo.create(
                    session=self.uow_service.session,
                    obj_in={
                        "organization_id": org_uuid,
                        "user_id": ctx.get_user_id_uuid(),
                        "provider": dto.provider,
                        "model_name": dto.model,
                        "prompt_tokens": dto.prompt_tokens,
                        "completion_tokens": dto.completion_tokens,
                        "total_tokens": total_tokens,
                        "cost_usd": Decimal(str(total_cost)),
                        "latency_ms": getattr(dto, "latency_ms", 100),
                        "status": status_val,
                        "request_id": getattr(dto, "request_id", None),
                    },
                    actor_id=ctx.get_user_id_str(),
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        AIUsageRecorded(
                            aggregate_id=str(org_id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            provider=dto.provider,
                            model=dto.model,
                            total_tokens=total_tokens,
                            calculated_cost_usd=total_cost,
                        )
                    )

            return ServiceResult.ok(data=True, status_code=201)

        except Exception as exc:
            logger.error(f"record_usage failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def get_usage_summary(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[UsageSummaryDTO]:
        try:
            AIUsagePolicy.can_view(self.authorizer, ctx, org_id)
            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                from api.repositories.ai_gateway_repository import AITokenUsageRepository
                repo = AITokenUsageRepository(organization_id=org_uuid)
                usages = await repo.find_many(session=self.uow_service.session)

                total_requests = len(usages)
                total_prompt_tokens = sum(u.prompt_tokens for u in usages)
                total_completion_tokens = sum(u.completion_tokens for u in usages)
                total_tokens = sum(u.total_tokens for u in usages)
                total_cost_usd = float(sum(u.cost_usd for u in usages))

                now = datetime.now(timezone.utc)
                period_start = min((u.created_at for u in usages), default=now)
                period_end = max((u.created_at for u in usages), default=now)

                dto = UsageSummaryDTO(
                    organization_id=org_uuid,
                    total_requests=total_requests,
                    total_prompt_tokens=total_prompt_tokens,
                    total_completion_tokens=total_completion_tokens,
                    total_tokens=total_tokens,
                    total_cost_usd=round(total_cost_usd, 6),
                    period_start=period_start,
                    period_end=period_end,
                )
                return ServiceResult.ok(data=dto)

        except Exception as exc:
            logger.error(f"get_usage_summary failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
