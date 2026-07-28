"""
EAIMOS Platform Cache Keys
===========================
Cache key functions for Billing, Analytics & Security Platform Services.
"""

from typing import Union
import uuid

BILLING_CACHE_PREFIX: str = "billing"
ANALYTICS_CACHE_PREFIX: str = "analytics"
SECURITY_CACHE_PREFIX: str = "security_platform"


def org_subscription_cache_key(org_id: Union[uuid.UUID, str]) -> str:
    return f"{BILLING_CACHE_PREFIX}:sub:org:{str(org_id)}"


def org_credits_cache_key(org_id: Union[uuid.UUID, str]) -> str:
    return f"{BILLING_CACHE_PREFIX}:credits:org:{str(org_id)}"
