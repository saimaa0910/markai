"""
Integrations Permissions.
"""

from enum import Enum


class IntegrationPermission(str, Enum):
    CONNECT = "integrations:connect"
    DISCONNECT = "integrations:disconnect"
