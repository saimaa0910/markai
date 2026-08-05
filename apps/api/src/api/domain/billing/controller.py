"""
Billing Controller.
"""

from typing import Dict, Any


class BillingController:
    async def get_subscription(self, org_id: str) -> Dict[str, Any]:
        return {"plan": "enterprise"}


billing_controller = BillingController()
