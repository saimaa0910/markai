"""
CRM Domain Controller.
"""

from typing import Dict, Any, List


class CRMController:
    async def get_contacts(self) -> List[Dict[str, Any]]:
        return []


crm_controller = CRMController()
