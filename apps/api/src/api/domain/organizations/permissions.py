"""
Organizations Permissions.
"""

from enum import Enum


class OrganizationPermission(str, Enum):
    OWNER = "org:owner"
    ADMIN = "org:admin"
    MEMBER = "org:member"
