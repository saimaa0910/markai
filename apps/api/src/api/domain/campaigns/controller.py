"""
Campaigns Domain Controller.
"""

from typing import Dict, Any, List


class CampaignController:
    async def get_campaigns(self) -> List[Dict[str, Any]]:
        return []


campaign_controller = CampaignController()
