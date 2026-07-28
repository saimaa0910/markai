"""
EAIMOS Observability Cache Keys
================================
Cache key functions for Observability, Telemetry & Incident Services.
"""

from typing import Union
import uuid

OBSERVABILITY_CACHE_PREFIX: str = "observability"


def trace_cache_key(trace_id: str) -> str:
    return f"{OBSERVABILITY_CACHE_PREFIX}:trace:{trace_id}"


def incident_cache_key(incident_id: Union[uuid.UUID, str]) -> str:
    return f"{OBSERVABILITY_CACHE_PREFIX}:incident:{str(incident_id)}"
