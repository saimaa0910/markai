"""
EAIMOS Model Router Service (Sprint 3)
========================================
Service Layer for LLM selection, cost estimation, capability matching, and fallback handling.
"""

import logging
from typing import Any, Dict, List, Optional
from api.services.base import ServiceContext, ServiceResult
from api.services.ai.constants import DEFAULT_MODEL_PER_PROVIDER, MODEL_PRICING_PER_1K
from api.services.ai.dtos import ModelRouteResultDTO, RouteRequestDTO
from api.services.ai.events import ModelFailoverTriggered, ModelRouted
from api.services.ai.policies import RouterPolicy
from api.services.ai.validators import validate_model_provider_supported

logger = logging.getLogger("eaimos.ai.router")


class ModelRouterService:
    """Intelligent Model Routing & Failover Service."""

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

    async def route_request(
        self,
        ctx: ServiceContext,
        dto: RouteRequestDTO,
    ) -> ServiceResult[ModelRouteResultDTO]:
        try:
            RouterPolicy.can_route(self.authorizer, ctx)

            provider = dto.preferred_provider or "openai"
            validate_model_provider_supported(provider)

            model = dto.preferred_model or DEFAULT_MODEL_PER_PROVIDER.get(provider, "gpt-4o")
            routing_strategy = "latency_cost_optimized"
            org_id = ctx.organization_id

            async with self.uow_service:
                if org_id:
                    from api.repositories.ai_gateway_repository import AIRoutingPolicyRepository
                    from api.repositories.filters import FilterParam, FilterOperator
                    repo = AIRoutingPolicyRepository(organization_id=org_id)
                    policies = await repo.find_many(
                        session=self.uow_service.session,
                        filters=[
                            FilterParam(field="is_active", operator=FilterOperator.EQ, value=True)
                        ]
                    )
                    # Filter by request type
                    matching_policy = None
                    for policy in sorted(policies, key=lambda p: p.priority, reverse=True):
                        req_type = getattr(dto, "request_type", None) or "chat"
                        if policy.request_type == "*" or policy.request_type.lower() == req_type.lower():
                            matching_policy = policy
                            break

                    if matching_policy:
                        routing_strategy = matching_policy.routing_strategy

                # Estimate cost
                pricing = MODEL_PRICING_PER_1K.get(model, {"input": 0.0025, "output": 0.01})
                total_chars = sum(len(str(m.get("content", ""))) for m in dto.messages)
                est_tokens = max(1, total_chars // 4)
                est_cost = (est_tokens / 1000.0) * pricing["input"]

                # Fallback chain
                fallbacks = ["google:gemini-1.5-flash", "groq:llama-3.3-70b-versatile"]
                primary_route = f"{provider}:{model}"
                if primary_route in fallbacks:
                    fallbacks.remove(primary_route)

                # Log routing decisions in the database
                from api.models.router import AIRoutingLog
                from api.repositories.base import BaseRepository
                log_repo = BaseRepository[AIRoutingLog](AIRoutingLog)
                log_data = {
                    "organization_id": org_id,
                    "user_id": ctx.user_id,
                    "request_type": getattr(dto, "request_type", None) or "chat",
                    "strategy_used": routing_strategy,
                    "selected_provider": provider,
                    "selected_model": model,
                    "fallback_count": len(fallbacks),
                    "retry_count": 0,
                    "latency_ms": 100,
                    "cost_usd": est_cost,
                    "prompt_tokens": est_tokens,
                    "completion_tokens": 0,
                    "success": True,
                }
                await log_repo.create(
                    session=self.uow_service.session,
                    obj_in=log_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        ModelRouted(
                            aggregate_id=ctx.get_user_id_str() or "system",
                            tenant_id=ctx.get_org_id_str(),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            selected_provider=provider,
                            selected_model=model,
                            estimated_cost_usd=round(est_cost, 6),
                        )
                    )

            result = ModelRouteResultDTO(
                selected_provider=provider,
                selected_model=model,
                fallback_chain=fallbacks,
                estimated_cost_usd=round(est_cost, 6),
                routing_strategy=routing_strategy,
            )

            return ServiceResult.ok(data=result)

        except Exception as exc:
            logger.error(f"route_request failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def record_failover(
        self,
        ctx: ServiceContext,
        failed_provider: str,
        failed_model: str,
        fallback_provider: str,
        fallback_model: str,
        error_message: Optional[str] = None,
        retry_attempts: int = 1,
    ) -> ServiceResult[bool]:
        try:
            async with self.uow_service:
                from api.models.router import AIFailoverEvent
                from api.repositories.base import BaseRepository
                repo = BaseRepository[AIFailoverEvent](AIFailoverEvent)
                data = {
                    "organization_id": ctx.organization_id,
                    "failed_provider": failed_provider,
                    "failed_model": failed_model,
                    "fallback_provider": fallback_provider,
                    "fallback_model": fallback_model,
                    "error_message": error_message,
                    "retry_attempts": retry_attempts,
                }
                await repo.create(
                    session=self.uow_service.session,
                    obj_in=data,
                    actor_id=ctx.get_user_id_uuid(),
                )
                if self.dispatcher:
                    await self.dispatcher.publish(
                        ModelFailoverTriggered(
                            aggregate_id=ctx.get_user_id_str() or "system",
                            tenant_id=ctx.get_org_id_str(),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            failed_provider=failed_provider,
                            failed_model=failed_model,
                            fallback_provider=fallback_provider,
                            fallback_model=fallback_model,
                        )
                    )
            return ServiceResult.ok(data=True)
        except Exception as exc:
            logger.error(f"record_failover failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
