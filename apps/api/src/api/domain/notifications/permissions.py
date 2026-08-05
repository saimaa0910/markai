"""
Notifications Permissions.
"""

from enum import Enum


class NotificationPermission(str, Enum):
    SEND = "notifications:send"
    READ = "notifications:read"
