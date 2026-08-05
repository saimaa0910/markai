"""
Campaigns DTO.
"""

from dataclasses import dataclass


@dataclass
class CampaignDTO:
    id: str
    name: str
    status: str
