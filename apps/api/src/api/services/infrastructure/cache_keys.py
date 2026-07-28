"""
EAIMOS Infrastructure Cache Keys
=================================
Cache key functions for File Storage, Notifications & Feature Flags.
"""

from typing import Union
import uuid

INFRA_CACHE_PREFIX: str = "infrastructure"


def file_asset_cache_key(file_id: Union[uuid.UUID, str]) -> str:
    return f"{INFRA_CACHE_PREFIX}:file:{str(file_id)}"


def feature_flag_cache_key(flag_key: str) -> str:
    return f"{INFRA_CACHE_PREFIX}:ff:{flag_key}"
