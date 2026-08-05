"""
Campaigns Domain Repository.
"""

from typing import List, Any


class CampaignRepository:
    async def get_all(self) -> List[Any]:
        return []


campaign_repository = CampaignRepository()
