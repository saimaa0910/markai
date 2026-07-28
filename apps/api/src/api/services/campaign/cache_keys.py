"""
EAIMOS Campaign Cache Keys
===========================
Cache key helpers and TTLs for Campaign & Content Management Services.
"""

from typing import Union
import uuid

CAMPAIGN_CACHE_PREFIX: str = "campaign"
AUDIENCE_CACHE_PREFIX: str = "audience"
VARIANT_CACHE_PREFIX: str = "variant"

CAMPAIGN_CACHE_TTL: int = 1800  # 30 mins


def campaign_cache_key(campaign_id: Union[uuid.UUID, str]) -> str:
    return f"{CAMPAIGN_CACHE_PREFIX}:{str(campaign_id)}"


def org_campaigns_list_key(org_id: Union[uuid.UUID, str]) -> str:
    return f"{CAMPAIGN_CACHE_PREFIX}:org:{str(org_id)}:list"


def audience_segment_cache_key(segment_id: Union[uuid.UUID, str]) -> str:
    return f"{AUDIENCE_CACHE_PREFIX}:{str(segment_id)}"
