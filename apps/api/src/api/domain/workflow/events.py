"""
Workflow Events.
"""

from dataclasses import dataclass


@dataclass
class WorkflowExecutedEvent:
    workflow_id: str
    status: str
