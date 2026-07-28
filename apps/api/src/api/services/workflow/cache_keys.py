"""
EAIMOS Workflow Cache Keys
===========================
Cache key functions and TTLs for Workflow & Agent Services.
"""

from typing import Union
import uuid

WORKFLOW_CACHE_PREFIX: str = "workflow"
AGENT_CACHE_PREFIX: str = "agent"

WORKFLOW_CACHE_TTL: int = 1800  # 30 mins


def workflow_def_cache_key(workflow_id: Union[uuid.UUID, str]) -> str:
    return f"{WORKFLOW_CACHE_PREFIX}:def:{str(workflow_id)}"


def org_workflows_list_key(org_id: Union[uuid.UUID, str]) -> str:
    return f"{WORKFLOW_CACHE_PREFIX}:org:{str(org_id)}:list"


def agent_cache_key(agent_id: Union[uuid.UUID, str]) -> str:
    return f"{AGENT_CACHE_PREFIX}:{str(agent_id)}"
