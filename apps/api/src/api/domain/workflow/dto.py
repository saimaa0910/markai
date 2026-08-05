"""
Workflow DTO.
"""

from dataclasses import dataclass


@dataclass
class WorkflowDTO:
    id: str
    name: str
