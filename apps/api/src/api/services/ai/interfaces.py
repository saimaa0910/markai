"""
EAIMOS AI Gateway Service Interfaces
=====================================
Protocol declarations for Sprint 3 AI services.
"""

from typing import Any, Dict, List, Optional, Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.ai.dtos import (
    CreatePromptDTO,
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
)


class IPromptService(Protocol):
    async def create_prompt(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreatePromptDTO
    ) -> ServiceResult[PromptResponseDTO]: ...

    async def get_prompt(
        self, ctx: ServiceContext, prompt_id: Union[uuid.UUID, str]
    ) -> ServiceResult[PromptResponseDTO]: ...

    async def render_prompt(
        self, ctx: ServiceContext, dto: RenderPromptDTO
    ) -> ServiceResult[RenderedPromptResponseDTO]: ...


class IModelRouterService(Protocol):
    async def route_request(
        self, ctx: ServiceContext, dto: RouteRequestDTO
    ) -> ServiceResult[ModelRouteResultDTO]: ...


class IRAGService(Protocol):
    async def index_document(
        self, ctx: ServiceContext, dto: IndexDocumentDTO
    ) -> ServiceResult[bool]: ...

    async def search(
        self, ctx: ServiceContext, dto: SearchQueryDTO
    ) -> ServiceResult[RAGSearchResultDTO]: ...


class IMemoryService(Protocol):
    async def store_message(
        self, ctx: ServiceContext, dto: StoreMessageDTO
    ) -> ServiceResult[bool]: ...

    async def get_memory(
        self, ctx: ServiceContext, conversation_id: Union[uuid.UUID, str]
    ) -> ServiceResult[ConversationMemoryDTO]: ...


class IAIUsageService(Protocol):
    async def record_usage(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: RecordUsageDTO
    ) -> ServiceResult[bool]: ...

    async def get_usage_summary(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str]
    ) -> ServiceResult[UsageSummaryDTO]: ...
