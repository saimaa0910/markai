"""
Analytics Permissions.
"""

from enum import Enum


class AnalyticsPermission(str, Enum):
    VIEW = "analytics:view"
    EXPORT = "analytics:export"
