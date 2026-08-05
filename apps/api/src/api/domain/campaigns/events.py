"""
Campaigns Events.
"""

from dataclasses import dataclass


@dataclass
class CampaignLaunchedEvent:
    campaign_id: str
    name: str
