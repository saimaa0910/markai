"""
Billing Permissions.
"""

from enum import Enum


class BillingPermission(str, Enum):
    MANAGE = "billing:manage"
    VIEW = "billing:view"
