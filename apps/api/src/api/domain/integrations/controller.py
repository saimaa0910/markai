"""
Integrations Controller.
"""

from typing import List, Dict, Any


class IntegrationsController:
    async def list_integrations(self) -> List[Dict[str, Any]]:
        return []


integrations_controller = IntegrationsController()
