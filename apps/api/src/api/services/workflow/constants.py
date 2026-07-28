"""
EAIMOS Workflow & Agent Constants
==================================
Constants for Sprint 5 Workflows, Agents & Integrations Services.
"""

from typing import Set

SUPPORTED_WORKFLOW_TRIGGERS: Set[str] = {"MANUAL", "SCHEDULED", "WEBHOOK", "CAMPAIGN_EVENT", "CRM_EVENT"}
SUPPORTED_WORKFLOW_STATUSES: Set[str] = {"DRAFT", "ACTIVE", "ARCHIVED"}
SUPPORTED_EXECUTION_STATUSES: Set[str] = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "WAITING"}

DEFAULT_WORKFLOW_MAX_RETRIES: int = 3
DEFAULT_WORKFLOW_TIMEOUT_SECONDS: int = 3600
MAX_AGENT_TOOL_CALLS_PER_TASK: int = 25
