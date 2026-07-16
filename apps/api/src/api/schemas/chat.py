import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ChatConversationCreate(BaseModel):
    title: Optional[str] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    provider_name: Optional[str] = None


class ChatConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None


class ChatConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    organization_id: uuid.UUID
    user_id: uuid.UUID
    is_archived: bool
    is_favorite: bool
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    provider_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True
