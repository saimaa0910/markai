"""
Workflow Model Entity.
"""

from pydantic import BaseModel
from typing import List, Dict, Any


class WorkflowDomainEntity(BaseModel):
    id: str
    name: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
