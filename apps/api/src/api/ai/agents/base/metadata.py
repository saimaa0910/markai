from typing import Optional
from pydantic import BaseModel
from api.ai.agents.base.constants import AgentStatus

class AgentMetadata(BaseModel):
    icon: str
    gradient: str
    accent_color: str
    category: str
    description: str
    author: str = "Viptant"
    version: str = "1.0.0"
    release_notes: Optional[str] = None
    status: AgentStatus = AgentStatus.STABLE
