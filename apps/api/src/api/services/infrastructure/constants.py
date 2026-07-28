"""
EAIMOS Infrastructure Constants
================================
Constants for Sprint 12 File Storage, Notifications & Feature Flags Services.
"""

from typing import Set

SUPPORTED_NOTIFICATION_TYPES: Set[str] = {"EMAIL", "SLACK", "IN_APP", "SMS"}
SUPPORTED_FEATURE_FLAG_STRATEGIES: Set[str] = {"BOOLEAN", "PERCENTAGE", "TENANT_ALLOWLIST"}
MAX_FILE_SIZE_BYTES: int = 52_428_800  # 50 MB
