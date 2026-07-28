"""
EAIMOS Workflow Service Layer (Sprint 5)
=========================================
Public API for Workflows, Agents & Integrations domain services.
"""

from api.services.workflow.workflow_engine_service import WorkflowEngineService
from api.services.workflow.agent_executor_service import AgentExecutorService
from api.services.workflow.integration_service import IntegrationService

from api.services.workflow.dtos import (
    CreateWorkflowDefinitionDTO,
    WorkflowDefinitionResponseDTO,
    TriggerWorkflowDTO,
    WorkflowExecutionResponseDTO,
    CreateAgentDTO,
    ExecuteAgentTaskDTO,
    AgentTaskResultDTO,
    RegisterWebhookDTO,
)

from api.services.workflow.events import (
    WorkflowDefinitionCreated,
    WorkflowExecutionStarted,
    WorkflowExecutionCompleted,
    AgentTaskStarted,
    AgentTaskCompleted,
)

from api.services.workflow.dependencies import (
    get_workflow_engine_service,
    get_agent_executor_service,
    get_integration_service,
)

__all__ = [
    "WorkflowEngineService",
    "AgentExecutorService",
    "IntegrationService",
    "CreateWorkflowDefinitionDTO",
    "WorkflowDefinitionResponseDTO",
    "TriggerWorkflowDTO",
    "WorkflowExecutionResponseDTO",
    "CreateAgentDTO",
    "ExecuteAgentTaskDTO",
    "AgentTaskResultDTO",
    "RegisterWebhookDTO",
    "get_workflow_engine_service",
    "get_agent_executor_service",
    "get_integration_service",
]
