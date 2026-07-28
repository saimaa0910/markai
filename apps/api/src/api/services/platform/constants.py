"""
EAIMOS Platform Constants
==========================
Constants for Sprint 6 Billing, Analytics & Security Platform Services.
"""

from typing import Set

SUPPORTED_PLAN_TIERS: Set[str] = {"FREE", "STARTER", "PROFESSIONAL", "ENTERPRISE"}
SUPPORTED_BILLING_CYCLES: Set[str] = {"MONTHLY", "ANNUAL", "USAGE"}
SUPPORTED_THREAT_SEVERITIES: Set[str] = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
