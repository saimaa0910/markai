"""
EAIMOS AI Gateway Dependency Providers
=======================================
FastAPI dependency injection factories for Sprint 3 AI services.
"""

from api.services.base.dependency_provider import container
from api.services.ai.prompt_service import PromptService
from api.services.ai.model_router_service import ModelRouterService
from api.services.ai.rag_service import RAGService
from api.services.ai.memory_service import MemoryService
from api.services.ai.ai_usage_service import AIUsageService
from api.services.ai.agui_execution_service import AGUIExecutionService


def get_prompt_service() -> PromptService:
    return PromptService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_model_router_service() -> ModelRouterService:
    return ModelRouterService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_rag_service() -> RAGService:
    return RAGService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_memory_service() -> MemoryService:
    return MemoryService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_ai_usage_service() -> AIUsageService:
    return AIUsageService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_agui_execution_service() -> AGUIExecutionService:
    return AGUIExecutionService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
