import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ChatConversationCreate(BaseModel):
    title: Optional[str] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    provider_name: Optional[str] = None
    is_pinned: Optional[bool] = False


class ChatConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None


class ChatConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    organization_id: uuid.UUID
    user_id: uuid.UUID
    is_archived: bool
    is_favorite: bool
    is_pinned: bool
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    provider_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatMessageCreate(BaseModel):
    content: str
    model_name: str
    provider: Optional[str] = None
    prompt_id: Optional[uuid.UUID] = None
    system_prompt: Optional[str] = None
    rag_enabled: Optional[bool] = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    json_mode: Optional[bool] = False
    stream: Optional[bool] = True
    attachment_ids: Optional[List[uuid.UUID]] = None


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    latency_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Extended Phase 2 Schemas ---

class ConversationBookmarkResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationShareCreate(BaseModel):
    permission: Optional[str] = "viewer"  # "viewer", "editor"


class ConversationShareResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    shared_by_id: uuid.UUID
    share_token: str
    permission: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatParticipantCreate(BaseModel):
    user_email: str
    role: Optional[str] = "member"  # "owner", "editor", "member", "viewer"


class ChatParticipantResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    user_email: Optional[str] = None
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatAttachmentResponse(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    storage_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSearchHighlight(BaseModel):
    message_id: uuid.UUID
    role: str
    snippet: str
    created_at: datetime


class ChatSearchResponse(BaseModel):
    conversation: ChatConversationResponse
    highlights: List[ChatSearchHighlight]


class ProviderUsageMetrics(BaseModel):
    provider: str
    tokens: int
    cost_usd: float
    percentage: float


class ModelUsageMetrics(BaseModel):
    model: str
    tokens: int
    cost_usd: float
    percentage: float


class DailyCostCoordinate(BaseModel):
    date: str
    cost_usd: float
    tokens: int
    messages: int


class ChatAnalyticsResponse(BaseModel):
    total_conversations: int
    total_messages: int
    active_users: int
    average_tokens_per_session: float
    average_cost_per_session: float
    average_latency_ms: float
    provider_usage: List[ProviderUsageMetrics]
    model_usage: List[ModelUsageMetrics]
    daily_stats: List[DailyCostCoordinate]
