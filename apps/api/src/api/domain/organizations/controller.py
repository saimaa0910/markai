"""
Organizations Domain Controller.
"""

from typing import Dict, Any


class OrganizationController:
    async def get_org_details(self, org_id: str) -> Dict[str, Any]:
        return {"id": org_id, "name": "Org Placeholder"}


org_controller = OrganizationController()
