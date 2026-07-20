import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from api.models.agent import AgentType, AgentStatus, AgentRunStatus


# --- AGENT DEFINITION SCHEMAS ---

class AgentDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    agent_type: Optional[AgentType] = AgentType.CUSTOM
    status: Optional[AgentStatus] = AgentStatus.ACTIVE
    system_prompt: Optional[str] = None
    prompt_template_name: Optional[str] = None
    allowed_tools: Optional[List[str]] = Field(default_factory=list)
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    reasoning_mode: Optional[str] = None
    execution_mode: Optional[str] = None
    memory_enabled: Optional[bool] = True
    max_memory_items: Optional[int] = 20
    max_iterations: Optional[int] = 10
    avatar: Optional[str] = None
    avatar_color: Optional[str] = None
    welcome_message: Optional[str] = None
    is_public: Optional[bool] = False
    is_favorite: Optional[bool] = False
    is_pinned: Optional[bool] = False


class AgentDefinitionCreate(AgentDefinitionBase):
    pass


class AgentDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[AgentType] = None
    status: Optional[AgentStatus] = None
    system_prompt: Optional[str] = None
    prompt_template_name: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    reasoning_mode: Optional[str] = None
    execution_mode: Optional[str] = None
    memory_enabled: Optional[bool] = None
    max_memory_items: Optional[int] = None
    max_iterations: Optional[int] = None
    avatar: Optional[str] = None
    avatar_color: Optional[str] = None
    welcome_message: Optional[str] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None


class AgentDefinitionResponse(AgentDefinitionBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


# --- AGENT SESSION SCHEMAS ---

class AgentSessionBase(BaseModel):
    agent_id: uuid.UUID
    title: str
    context: Optional[Dict[str, Any]] = None


class AgentSessionCreate(AgentSessionBase):
    pass


class AgentSessionUpdate(BaseModel):
    title: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentSessionResponse(AgentSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True


# --- AGENT RUN SCHEMAS ---

class AgentRunCreate(BaseModel):
    user_input: str


class AgentRunResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    organization_id: uuid.UUID
    user_input: str
    agent_output: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    status: AgentRunStatus
    error_message: Optional[str] = None
    iterations: int
    total_tokens: int
    latency_ms: Optional[int] = None

    class Config:
        from_attributes = True


# --- AGENT LOG SCHEMAS ---

class AgentLogResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    organization_id: uuid.UUID
    level: str
    step_type: str
    content: str
    meta_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
