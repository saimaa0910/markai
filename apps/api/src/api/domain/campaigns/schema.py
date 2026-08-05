"""
Campaigns Pydantic Schemas.
"""

from pydantic import BaseModel
from typing import List


class CampaignResponseSchema(BaseModel):
    id: str
    name: str
    status: str
    channels: List[str]
