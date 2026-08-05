"""
Billing Model Entity.
"""

from pydantic import BaseModel


class SubscriptionDomainEntity(BaseModel):
    id: str
    org_id: str
    plan_name: str
    credits_remaining: int
