"""
Auth Domain Permissions & Scope Definitions.
"""

from enum import Enum


class AuthScope(str, Enum):
    READ = "auth:read"
    WRITE = "auth:write"
    ADMIN = "auth:admin"
