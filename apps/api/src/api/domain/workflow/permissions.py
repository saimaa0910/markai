"""
Workflow Permissions.
"""

from enum import Enum


class WorkflowPermission(str, Enum):
    EXECUTE = "workflow:execute"
    EDIT = "workflow:edit"
