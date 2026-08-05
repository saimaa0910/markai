"""
CRM Permissions.
"""

from enum import Enum


class CRMPermission(str, Enum):
    READ = "crm:read"
    WRITE = "crm:write"
    DELETE = "crm:delete"
