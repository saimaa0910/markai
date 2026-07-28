"""
EAIMOS Workflow Domain Events
==============================
Domain events for Sprint 5 Workflows, Agents & Integrations.
"""

from typing import Optional
from api.services.base.events import DomainEvent


class WorkflowDefinitionCreated(DomainEvent):
    event_type: str = "workflow.definition_created"
    workflow_id: str = ""
    name: str = ""
    trigger: str = ""


class WorkflowExecutionStarted(DomainEvent):
    event_type: str = "workflow.execution_started"
    execution_id: str = ""
    workflow_id: str = ""


class WorkflowExecutionCompleted(DomainEvent):
    event_type: str = "workflow.execution_completed"
    execution_id: str = ""
    workflow_id: str = ""


class AgentTaskStarted(DomainEvent):
    event_type: str = "agent.task_started"
    agent_id: str = ""


class AgentTaskCompleted(DomainEvent):
    event_type: str = "agent.task_completed"
    agent_id: str = ""
    tool_calls_count: int = 0
