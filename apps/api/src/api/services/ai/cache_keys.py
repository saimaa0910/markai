"""
EAIMOS AI Gateway Cache Keys
=============================
Structured cache key functions and TTLs for AI Gateway & Orchestration.
"""

from typing import Union, Optional
import uuid

AI_CACHE_PREFIX: str = "ai"
PROMPT_PREFIX: str = f"{AI_CACHE_PREFIX}:prompt"
ROUTER_PREFIX: str = f"{AI_CACHE_PREFIX}:router"
RAG_PREFIX: str = f"{AI_CACHE_PREFIX}:rag"
MEMORY_PREFIX: str = f"{AI_CACHE_PREFIX}:memory"
USAGE_PREFIX: str = f"{AI_CACHE_PREFIX}:usage"

# TTLs (seconds)
PROMPT_CACHE_TTL: int = 1800        # 30 mins
MODEL_CONFIG_CACHE_TTL: int = 3600  # 1 hour
RAG_QUERY_CACHE_TTL: int = 600      # 10 mins
MEMORY_BUFFER_CACHE_TTL: int = 900  # 15 mins
USAGE_QUOTA_CACHE_TTL: int = 60     # 1 min (frequently changing)


def prompt_template_cache_key(prompt_id: Union[uuid.UUID, str], version: Optional[int] = None) -> str:
    v_str = f":v{version}" if version is not None else ":latest"
    return f"{PROMPT_PREFIX}:{str(prompt_id)}{v_str}"


def org_prompts_list_key(org_id: Union[uuid.UUID, str]) -> str:
    return f"{PROMPT_PREFIX}:org:{str(org_id)}:list"


def model_route_config_cache_key(org_id: Union[uuid.UUID, str]) -> str:
    return f"{ROUTER_PREFIX}:config:org:{str(org_id)}"


def conversation_memory_cache_key(conversation_id: Union[uuid.UUID, str]) -> str:
    return f"{MEMORY_PREFIX}:{str(conversation_id)}"


def org_usage_quota_cache_key(org_id: Union[uuid.UUID, str]) -> str:
    return f"{USAGE_PREFIX}:quota:org:{str(org_id)}"


def invalidate_pattern_for_org_prompts(org_id: Union[uuid.UUID, str]) -> str:
    return f"{PROMPT_PREFIX}:org:{str(org_id)}:*"
