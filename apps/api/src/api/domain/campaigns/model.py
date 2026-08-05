"""
Campaigns Domain Model Entity.
"""

from pydantic import BaseModel
from typing import List, Optional


class CampaignDomainEntity(BaseModel):
    id: str
    name: str
    status: str
    channels: List[str]
