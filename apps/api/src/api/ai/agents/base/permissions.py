from typing import List, Optional
from pydantic import BaseModel, Field

class AgentPermissions(BaseModel):
    allowed_tools: List[str] = Field(default_factory=list)
    allowed_integrations: List[str] = Field(default_factory=list)
    allowed_apis: List[str] = Field(default_factory=list)
    allowed_organizations: List[str] = Field(default_factory=lambda: ["*"])
    allowed_roles: List[str] = Field(default_factory=lambda: ["*"])
    allowed_users: List[str] = Field(default_factory=lambda: ["*"])
