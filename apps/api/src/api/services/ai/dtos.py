"""
EAIMOS AI Gateway Data Transfer Objects (DTOs)
================================================
Pydantic v2 DTOs for Sprint 3 AI Gateway & Orchestration Services.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Prompt Management DTOs
# =============================================================================

class CreatePromptCollectionDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    visibility: str = Field("ORGANIZATION", description="ORGANIZATION | TEAM | PRIVATE | PUBLIC")


class CreatePromptFolderDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    collection_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None


class CreatePromptDTO(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    template: str = Field(..., min_length=1, max_length=50000)
    description: Optional[str] = None
    collection_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    tags: List[str] = Field(default_factory=list)
    variables: List[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    default_provider: Optional[str] = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    visibility: str = Field("ORGANIZATION")


class UpdatePromptDTO(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    template: Optional[str] = Field(None, min_length=1, max_length=50000)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    change_log: Optional[str] = None


class PromptResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    collection_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    title: str
    template: str
    description: Optional[str] = None
    version: int
    is_active: bool
    is_archived: bool
    is_favorite: bool
    is_pinned: bool
    visibility: str
    tags: List[str] = Field(default_factory=list)
    variables: List[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    default_provider: Optional[str] = None
    temperature: float
    top_p: float
    max_tokens: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RenderPromptDTO(BaseModel):
    prompt_id: uuid.UUID
    variables: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[int] = None


class RenderedPromptResponseDTO(BaseModel):
    prompt_id: uuid.UUID
    title: str
    rendered_text: str
    unresolved_variables: List[str] = Field(default_factory=list)
    version: int


# =============================================================================
# Model Router DTOs
# =============================================================================

class ModelChoiceDTO(BaseModel):
    provider: str
    model: str
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: Optional[int] = None


class RouteRequestDTO(BaseModel):
    messages: List[Dict[str, Any]]
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    require_capabilities: List[str] = Field(default_factory=list) # e.g. ["tools", "json", "vision"]
    max_cost_usd: Optional[float] = None
    max_latency_ms: Optional[int] = None


class ModelRouteResultDTO(BaseModel):
    selected_provider: str
    selected_model: str
    fallback_chain: List[str] = Field(default_factory=list)
    estimated_cost_usd: float
    routing_strategy: str


# =============================================================================
# RAG Engine DTOs
# =============================================================================

class IndexDocumentDTO(BaseModel):
    knowledge_base_id: uuid.UUID
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_size: int = 1000
    chunk_overlap: int = 200


class SearchQueryDTO(BaseModel):
    knowledge_base_ids: List[uuid.UUID]
    query_text: str
    top_k: int = Field(5, ge=1, le=50)
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    metadata_filter: Optional[Dict[str, Any]] = None


class RAGSearchResultItemDTO(BaseModel):
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    text_content: str
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGSearchResultDTO(BaseModel):
    query_text: str
    results: List[RAGSearchResultItemDTO]
    total_found: int
    execution_time_ms: float


# =============================================================================
# Conversational Memory DTOs
# =============================================================================

class StoreMessageDTO(BaseModel):
    conversation_id: uuid.UUID
    role: str = Field(..., description="user | assistant | system | tool")
    content: str
    name: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ConversationMemoryDTO(BaseModel):
    conversation_id: uuid.UUID
    messages: List[Dict[str, Any]]
    summary: Optional[str] = None
    total_tokens: int


# =============================================================================
# AI Usage & Token Metering DTOs
# =============================================================================

class RecordUsageDTO(BaseModel):
    provider: str
    model: str
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    execution_time_ms: float = Field(..., ge=0.0)
    is_error: bool = False
    error_code: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    prompt_id: Optional[uuid.UUID] = None


class UsageSummaryDTO(BaseModel):
    organization_id: uuid.UUID
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float
    period_start: datetime
    period_end: datetime


# =============================================================================
# AGUI Execution Protocol DTOs
# =============================================================================

class ExecutePromptDTO(BaseModel):
    prompt_id: uuid.UUID
    variables: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[uuid.UUID] = None
    stream: bool = True
    provider_override: Optional[str] = None
    model_override: Optional[str] = None
