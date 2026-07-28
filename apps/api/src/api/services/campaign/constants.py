"""
EAIMOS Campaign & Content Constants
====================================
Constants for Sprint 4 Campaign & Content Management Services.
"""

from typing import Set

SUPPORTED_CAMPAIGN_STATUSES: Set[str] = {"DRAFT", "SCHEDULED", "ACTIVE", "COMPLETED", "ARCHIVED"}
SUPPORTED_CAMPAIGN_CHANNELS: Set[str] = {"EMAIL", "SOCIAL", "ADS"}
SUPPORTED_CURRENCIES: Set[str] = {"USD", "EUR", "GBP", "CAD", "AUD"}

MAX_CAMPAIGN_BUDGET: float = 1_000_000.00
MIN_CAMPAIGN_BUDGET: float = 0.0

DEFAULT_AUDIENCE_SEGMENT_SIZE_LIMIT: int = 100_000
