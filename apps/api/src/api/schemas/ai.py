import uuid
from typing import Optional
from pydantic import BaseModel


# --- PROMPT SCHEMAS ---


class PromptBase(BaseModel):
    name: str
    content: str
    version: Optional[int] = 1


class PromptCreate(PromptBase):
    pass


class PromptResponse(PromptBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


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
    model_used: str


class MessageCreate(BaseModel):
    content: str
    model_name: str
    prompt_id: Optional[uuid.UUID] = None  # Optional prompt template applied


class MessageResponse(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID

    class Config:
        from_attributes = True
