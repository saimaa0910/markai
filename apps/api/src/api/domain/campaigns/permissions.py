"""
Campaigns Permissions.
"""

from enum import Enum


class CampaignPermission(str, Enum):
    READ = "campaigns:read"
    WRITE = "campaigns:write"
    DELETE = "campaigns:delete"
