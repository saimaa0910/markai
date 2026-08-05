"""
Billing Pydantic Schemas.
"""

from pydantic import BaseModel


class SubscriptionResponseSchema(BaseModel):
    id: str
    plan_name: str
    credits_remaining: int
