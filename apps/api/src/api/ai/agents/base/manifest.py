from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata

class AgentManifest(BaseModel):
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "MARKETING"
    tags: List[str] = Field(default_factory=list)
    icon: str = "🤖"
    color: str = "#7c3aed"
    owner: str = "Viptant"
    visibility: str = "public"
    capabilities: List[str] = Field(default_factory=list)
    supported_providers: List[str] = Field(default_factory=list)
    supported_models: List[str] = Field(default_factory=list)
    supported_tools: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    default_prompt: str = ""
    default_model: str = "gemini-1.5-flash"
    default_temperature: float = 0.7
    default_max_tokens: Optional[int] = None
    memory_requirements: Dict[str, Any] = Field(default_factory=dict)
    knowledge_requirements: Dict[str, Any] = Field(default_factory=dict)
    streaming_support: bool = True
    reflection_support: bool = True
    evaluation_support: bool = True
    telemetry_support: bool = True
    policies: AgentPolicies = Field(default_factory=AgentPolicies)
    permissions: AgentPermissions = Field(default_factory=AgentPermissions)
    metadata: AgentMetadata
    memory_strategy: str = "window"
    planner_strategy: str = "sequential"
    evaluation_strategy: str = "content"
