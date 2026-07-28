"""
EAIMOS CRM Cache Keys
======================
Cache key functions for CRM & Sales Pipeline Services.
"""

from typing import Union
import uuid

CRM_CACHE_PREFIX: str = "crm"


def pipeline_cache_key(pipeline_id: Union[uuid.UUID, str]) -> str:
    return f"{CRM_CACHE_PREFIX}:pipeline:{str(pipeline_id)}"


def deal_cache_key(deal_id: Union[uuid.UUID, str]) -> str:
    return f"{CRM_CACHE_PREFIX}:deal:{str(deal_id)}"


def lead_cache_key(lead_id: Union[uuid.UUID, str]) -> str:
    return f"{CRM_CACHE_PREFIX}:lead:{str(lead_id)}"
