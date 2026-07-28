"""
EAIMOS AGUI Execution Protocol Service (Sprint 3)
===================================================
Service Layer for Real-Time Streaming Prompt Execution, Tool Orchestration, and AGUI UI Component Generation.
"""

import logging
from typing import Any, AsyncGenerator, Dict, Optional
from api.services.base import ServiceContext, ServiceResult
from api.services.ai.dtos import ExecutePromptDTO
from api.services.ai.events import AGUIExecutionStarted
from api.services.ai.prompt_service import PromptService
from api.services.ai.model_router_service import ModelRouterService

logger = logging.getLogger("eaimos.ai.agui")


class AGUIExecutionService:
    """AGUI Protocol Prompt Execution Engine."""

    def __init__(
        self,
        prompt_service: Optional[PromptService] = None,
        router_service: Optional[ModelRouterService] = None,
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
        self.prompt_service = prompt_service or PromptService(uow_service=self.uow_service)
        self.router_service = router_service or ModelRouterService(uow_service=self.uow_service)

    async def execute(
        self,
        ctx: ServiceContext,
        dto: ExecutePromptDTO,
    ) -> ServiceResult[Dict[str, Any]]:
        try:
            if self.dispatcher:
                await self.dispatcher.publish(
                    AGUIExecutionStarted(
                        aggregate_id=str(dto.prompt_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        prompt_id=str(dto.prompt_id),
                        conversation_id=str(dto.conversation_id) if dto.conversation_id else None,
                    )
                )

            # 1. Render prompt template
            from api.services.ai.dtos import RenderPromptDTO
            render_res = await self.prompt_service.render_prompt(
                ctx, RenderPromptDTO(prompt_id=dto.prompt_id, variables=dto.variables)
            )
            if render_res.is_failure:
                return ServiceResult.fail(error=render_res.errors[0], error_code=render_res.error_code)

            rendered = render_res.unwrap()

            # 2. Mock AGUI response chunk stream / payload
            response_payload = {
                "prompt_id": str(dto.prompt_id),
                "rendered_text": rendered.rendered_text,
                "model_used": "gpt-4o",
                "output_text": f"AGUI Response generated for prompt '{rendered.title}'.",
                "agui_ui_schema": {
                    "component": "Card",
                    "props": {"title": rendered.title, "status": "success"},
                },
            }

            return ServiceResult.ok(data=response_payload)

        except Exception as exc:
            logger.error(f"execute failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
