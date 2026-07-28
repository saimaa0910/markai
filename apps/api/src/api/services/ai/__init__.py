"""
EAIMOS AI Gateway Service Layer (Sprint 3)
===========================================
Public API for the AI Gateway & LLM Orchestration domain service module.
"""

from api.services.ai.prompt_service import PromptService
from api.services.ai.model_router_service import ModelRouterService
from api.services.ai.rag_service import RAGService
from api.services.ai.memory_service import MemoryService
from api.services.ai.ai_usage_service import AIUsageService
from api.services.ai.agui_execution_service import AGUIExecutionService

from api.services.ai.dtos import (
    CreatePromptDTO,
    UpdatePromptDTO,
    PromptResponseDTO,
    RenderPromptDTO,
    RenderedPromptResponseDTO,
    RouteRequestDTO,
    ModelRouteResultDTO,
    IndexDocumentDTO,
    SearchQueryDTO,
    RAGSearchResultDTO,
    StoreMessageDTO,
    ConversationMemoryDTO,
    RecordUsageDTO,
    UsageSummaryDTO,
    ExecutePromptDTO,
)

from api.services.ai.events import (
    PromptTemplateCreated,
    PromptVersionPublished,
    ModelRouted,
    ModelFailoverTriggered,
    DocumentIndexed,
    VectorSearchExecuted,
    ConversationMemoryUpdated,
    MemorySummarized,
    AIUsageRecorded,
    AGUIExecutionStarted,
)

from api.services.ai.dependencies import (
    get_prompt_service,
    get_model_router_service,
    get_rag_service,
    get_memory_service,
    get_ai_usage_service,
    get_agui_execution_service,
)

__all__ = [
    "PromptService",
    "ModelRouterService",
    "RAGService",
    "MemoryService",
    "AIUsageService",
    "AGUIExecutionService",
    "CreatePromptDTO",
    "PromptResponseDTO",
    "RenderPromptDTO",
    "RenderedPromptResponseDTO",
    "RouteRequestDTO",
    "ModelRouteResultDTO",
    "IndexDocumentDTO",
    "SearchQueryDTO",
    "RAGSearchResultDTO",
    "StoreMessageDTO",
    "ConversationMemoryDTO",
    "RecordUsageDTO",
    "UsageSummaryDTO",
    "ExecutePromptDTO",
    "get_prompt_service",
    "get_model_router_service",
    "get_rag_service",
    "get_memory_service",
    "get_ai_usage_service",
    "get_agui_execution_service",
]
