"""
EAIMOS Chat & Real-time Messaging DTOs
=======================================
Pydantic v2 DTOs for Sprint 10 Conversational AI & Real-time Messaging.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Conversation DTOs
# =============================================================================

class CreateConversationDTO(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    system_prompt: Optional[str] = None
    model_name: Optional[str] = "gemini-2.5-flash"
    provider_name: Optional[str] = "google"
    temperature: float = Field(0.7, ge=0.0, le=2.0)


class ConversationResponseDTO(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    provider_name: Optional[str] = None
    temperature: Optional[float] = 0.7
    is_archived: bool = False
    is_favorite: bool = False
    is_pinned: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Message DTOs
# =============================================================================

class SendMessageDTO(BaseModel):
    conversation_id: uuid.UUID
    role: str = Field("USER", description="USER | ASSISTANT | SYSTEM | TOOL")
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageResponseDTO(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    token_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Stream Chunk DTOs
# =============================================================================

class StreamChunkDTO(BaseModel):
    conversation_id: uuid.UUID
    delta_text: str
    finish_reason: Optional[str] = None
