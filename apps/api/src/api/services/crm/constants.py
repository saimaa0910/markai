"""
EAIMOS CRM & Sales Pipeline Constants
=======================================
Constants for Sprint 9 CRM & Sales Pipeline Services.
"""

from typing import Set

SUPPORTED_DEAL_STATUSES: Set[str] = {"OPEN", "WON", "LOST"}
SUPPORTED_LEAD_STATUSES: Set[str] = {"NEW", "CONTACTED", "QUALIFIED", "UNQUALIFIED", "CONVERTED"}
DEFAULT_CURRENCY: str = "USD"
MIN_LEAD_SCORE: int = 0
MAX_LEAD_SCORE: int = 100
