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

    async def execute_prompt(
        self,
        dto: Any,
        rendered_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a rendered prompt through the real AI Gateway (P2-3).
        Returns a structured payload including the model response and an AGUI
        UI schema derived from the response rather than a mock payload.
        """
        try:
            from api.ai.gateway.coordinator import AIGateway

            # Resolve provider/model overrides.
            model_override = getattr(dto, "model_override", None)

            conversation_id = getattr(dto, "conversation_id", None)
            request_id = str(conversation_id or uuid.uuid4())

            org_id = self.uow_service.organization_id if self.uow_service else None
            user_id = self.uow_service.user_id if self.uow_service else None

            messages = [{"role": "user", "content": rendered_text or ""}]
            if not rendered_text:
                messages = [{"role": "user", "content": "Execute the request."}]

            gateway = AIGateway()

            def _run():
                from api.database.session import SessionLocal
                kwargs = {}
                if model_override:
                    kwargs["model_name"] = model_override
                with SessionLocal() as db:
                    return gateway.chat(
                        db=db,
                        messages=messages,
                        organization_id=uuid.UUID(str(org_id)) if org_id else uuid.uuid4(),
                        user_id=uuid.UUID(str(user_id)) if user_id else uuid.uuid4(),
                        temperature=0.7,
                        request_id=request_id,
                        **kwargs,
                    )

            import asyncio
            response = await asyncio.to_thread(_run)

            # Build AGUI UI schema from the real model response (P2-3).
            content = response.get("content", "")
            ui_schema = self._build_agui_ui_schema(content)

            return {
                "content": content,
                "prompt_tokens": response.get("prompt_tokens", 0),
                "completion_tokens": response.get("completion_tokens", 0),
                "cost_usd": response.get("cost_usd", 0),
                "model": response.get("model"),
                "provider": response.get("provider"),
                "latency_ms": response.get("latency_ms", 0),
                "request_id": request_id,
                "ui_schema": ui_schema,
            }
        except Exception as exc:
            logger.error(f"execute_prompt failed: {exc}", exc_info=True)
            raise

    @staticmethod
    def _build_agui_ui_schema(content: str) -> Dict[str, Any]:
        """Derive a lightweight AGUI render schema from a model response (P2-3)."""
        text = (content or "").strip()
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return {"type": "text", "value": text}
        if text.startswith(("```json", "{", "[")):
            return {"type": "json", "value": text}
        return {
            "type": "markdown",
            "blocks": [{"type": "paragraph", "content": p} for p in paragraphs[:10]],
        }

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
