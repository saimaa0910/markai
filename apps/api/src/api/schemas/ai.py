import uuid
from typing import Optional, List, Union, Dict, Any
from pydantic import BaseModel


# --- PROMPT SCHEMAS ---


class PromptBase(BaseModel):
    name: str
    content: str
    version: Optional[int] = 1
    category: Optional[str] = None
    tags: Optional[Union[str, List[str]]] = None
    description: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None
    is_shared: Optional[bool] = True


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[Union[str, List[str]]] = None
    description: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None
    is_shared: Optional[bool] = None
    status: Optional[str] = None
    change_log: Optional[str] = None


class PromptResponse(BaseModel):
    id: uuid.UUID
    name: str
    content: str
    version: Optional[int] = 1
    category: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None
    is_shared: Optional[bool] = True
    organization_id: uuid.UUID
    is_archived: Optional[bool] = False
    is_favorite: Optional[bool] = False
    is_pinned: Optional[bool] = False
    status: Optional[str] = "approved"
    change_log: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class PromptCollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    visibility: Optional[str] = "ORGANIZATION"


class PromptCollectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_archived: bool
    is_favorite: bool
    is_pinned: bool
    visibility: str
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


class PromptFolderCreate(BaseModel):
    name: str
    collection_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None


class PromptFolderResponse(BaseModel):
    id: uuid.UUID
    name: str
    collection_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


class PromptTestCaseCreate(BaseModel):
    name: str
    inputs: dict
    expected_output: Optional[str] = None


class PromptTestCaseResponse(BaseModel):
    id: uuid.UUID
    prompt_id: Optional[uuid.UUID] = None
    name: str
    inputs: dict
    expected_output: Optional[str] = None
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


class PromptEvaluationResponse(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    test_case_id: uuid.UUID
    model_name: str
    actual_output: Optional[str] = None
    correctness_score: Optional[float] = None
    grounding_score: Optional[float] = None
    relevance_score: Optional[float] = None
    consistency_score: Optional[float] = None
    safety_score: Optional[float] = None
    hallucination_risk: Optional[float] = None
    overall_score: Optional[float] = None
    status: str
    latency_ms: int
    cost_usd: float
    tokens_used: int

    class Config:
        from_attributes = True


class PromptExecuteRequest(BaseModel):
    variables: dict
    version: Optional[int] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    rag_enabled: Optional[bool] = False
    temperature: Optional[float] = 0.7


class PromptOptimizeRequest(BaseModel):
    content: str


class PromptImportRequest(BaseModel):
    file_content: str
    format_type: str


# --- CONVERSATION SCHEMAS ---


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


# --- MESSAGE SCHEMAS ---


class MessageBase(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str
    model_used: Optional[str] = None


class MessageCreate(BaseModel):
    content: str
    model_name: str
    prompt_id: Optional[uuid.UUID] = None  # Optional prompt template applied
    system_prompt: Optional[str] = None
    rag_enabled: Optional[bool] = False


class MessageResponse(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    provider_used: Optional[str] = None
    latency_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost_usd: Optional[float] = None

    class Config:
        from_attributes = True


# --- KNOWLEDGE SCHEMAS ---


class KnowledgeUploadRequest(BaseModel):
    title: str
    file_type: str  # pdf, docx, csv, md, url
    content: str


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    content: str
    document_id: uuid.UUID

    class Config:
        from_attributes = True


class KnowledgeDocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    file_type: str
    organization_id: uuid.UUID
    chunks: List[DocumentChunkResponse]

    class Config:
        from_attributes = True


class KnowledgeDocumentListElement(BaseModel):
    id: uuid.UUID
    name: str
    file_type: str
    status: str
    chunk_count: int
    file_size: int
    created_at: str
    collection_name: str

    class Config:
        from_attributes = True


class QuerySimilarChunksRequest(BaseModel):
    query_text: str
    limit: Optional[int] = 3


# --- MODEL REGISTRY SCHEMAS ---

class ModelRegistryResponse(BaseModel):
    id: uuid.UUID
    provider: str
    model_name: str
    context_window: int
    supports_streaming: bool
    supports_vision: bool
    supports_json: bool
    supports_images: bool
    supports_audio: bool
    supports_tool_calling: bool
    supports_embeddings: bool
    input_token_price: float
    output_token_price: float
    latency: float
    priority: int
    is_healthy: bool
    organization_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ModelRegistryUpdate(BaseModel):
    is_healthy: Optional[bool] = None
    priority: Optional[int] = None


# --- ROUTING RULE SCHEMAS ---

class RoutingRuleResponse(BaseModel):
    id: uuid.UUID
    request_type: str
    model_registry_id: uuid.UUID
    is_active: bool
    organization_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class RoutingRuleCreate(BaseModel):
    request_type: str
    model_registry_id: uuid.UUID
    is_active: Optional[bool] = True
    organization_id: Optional[uuid.UUID] = None


class RoutingRuleUpdate(BaseModel):
    request_type: Optional[str] = None
    model_registry_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


# --- TOKEN USAGE SCHEMAS ---

import datetime
class TokenUsageResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- PLAYGROUND RUN SCHEMAS ---

class PlaygroundRunRequest(BaseModel):
    system_prompt: Optional[str] = None
    user_prompt: str
    model_name: str


class PlaygroundRunResponse(BaseModel):
    output: str
    provider: str
    model: str
    tokens_used: int
    cost_usd: float
    latency_ms: int


# --- PROVIDER SCHEMAS ---

class ProviderResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    priority: int
    config: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ProviderCreate(BaseModel):
    name: str
    is_active: Optional[bool] = True
    priority: Optional[int] = 1


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class ProviderHealthResponse(BaseModel):
    provider_name: str
    is_healthy: bool
    latency: float
    last_checked: datetime.datetime
    error_message: Optional[str] = None


# --- PLAYGROUND REAL SCHEMAS ---

from typing import Dict
class PlaygroundChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model_name: str
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None


# --- COMPARE SCHEMAS ---

class CompareRequest(BaseModel):
    prompt: str
    model_names: List[str]
    system_prompt: Optional[str] = None
    category: Optional[str] = "text"


class CompareResponseElement(BaseModel):
    model_name: str
    provider: str
    response: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    status: str
    error_message: Optional[str] = None


class CompareResponse(BaseModel):
    results: List[CompareResponseElement]


# --- ROUTER SCHEMAS ---

class RouterSettingsResponse(BaseModel):
    routing_mode: str
    fallback_provider: Optional[str] = None
    is_active: bool
    default_text_provider: Optional[str] = None
    default_image_provider: Optional[str] = None
    default_video_provider: Optional[str] = None
    default_audio_provider: Optional[str] = None
    default_speech_provider: Optional[str] = None
    default_embeddings_provider: Optional[str] = None
    default_vision_provider: Optional[str] = None
    default_ocr_provider: Optional[str] = None
    default_moderation_provider: Optional[str] = None
    default_multimodal_provider: Optional[str] = None


class RouterSettingsUpdate(BaseModel):
    routing_mode: Optional[str] = None
    fallback_provider: Optional[str] = None
    is_active: Optional[bool] = None
    default_text_provider: Optional[str] = None
    default_image_provider: Optional[str] = None
    default_video_provider: Optional[str] = None
    default_audio_provider: Optional[str] = None
    default_speech_provider: Optional[str] = None
    default_embeddings_provider: Optional[str] = None
    default_vision_provider: Optional[str] = None
    default_ocr_provider: Optional[str] = None
    default_moderation_provider: Optional[str] = None
    default_multimodal_provider: Optional[str] = None

# --- PROMPT PLATFORM EXTENDED SCHEMAS ---

class PromptShareRequest(BaseModel):
    visibility: str = "organization"  # private, organization, public
    expires_in_days: Optional[int] = None
    is_editable: Optional[bool] = False


class PromptShareResponse(BaseModel):
    share_token: str
    share_url: str
    visibility: str
    expires_at: Optional[str] = None
    is_editable: bool


class PromptBulkActionRequest(BaseModel):
    action: str  # archive, restore, delete, permanent_delete, tag
    prompt_names: List[str]
    payload: Optional[Dict[str, Any]] = None


class PromptSearchRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    tag: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = False
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None
