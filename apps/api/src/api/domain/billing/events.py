"""
Billing Events.
"""

from dataclasses import dataclass


@dataclass
class SubscriptionUpgradedEvent:
    org_id: str
    new_plan: str
