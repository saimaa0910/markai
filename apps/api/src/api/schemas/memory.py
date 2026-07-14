import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel
from api.models.memory import MemoryType


# --- AGENT MEMORY SCHEMAS ---

class AgentMemoryBase(BaseModel):
    agent_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    memory_type: Optional[MemoryType] = MemoryType.SHORT_TERM
    memory_key: str
    memory_value: str
    importance: Optional[float] = 0.5


class AgentMemoryCreate(AgentMemoryBase):
    pass


class AgentMemoryResponse(AgentMemoryBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    access_count: int

    class Config:
        from_attributes = True


# --- CONVERSATION MEMORY SCHEMAS ---

class ConversationMemoryBase(BaseModel):
    session_id: uuid.UUID
    summary: str
    turns_covered: Optional[int] = 0
    summary_turn_index: Optional[int] = 0


class ConversationMemoryCreate(ConversationMemoryBase):
    pass


class ConversationMemoryResponse(ConversationMemoryBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


# --- ORGANIZATION MEMORY SCHEMAS ---

class OrganizationMemoryBase(BaseModel):
    category: str
    key: str
    value: str
    is_active: Optional[bool] = True
    meta_data: Optional[Dict[str, Any]] = None


class OrganizationMemoryCreate(OrganizationMemoryBase):
    pass


class OrganizationMemoryUpdate(BaseModel):
    category: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    is_active: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


class OrganizationMemoryResponse(OrganizationMemoryBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True
