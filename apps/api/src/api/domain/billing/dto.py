"""
Billing DTO.
"""

from dataclasses import dataclass


@dataclass
class SubscriptionDTO:
    id: str
    plan: str
