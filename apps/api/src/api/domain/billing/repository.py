"""
Billing Repository.
"""

from typing import Optional, Any


class BillingRepository:
    async def find_subscription(self, org_id: str) -> Optional[Any]:
        return None


billing_repository = BillingRepository()
