"""
EAIMOS Workflow Service Interfaces
===================================
Protocol declarations for Sprint 5 Workflow services.
"""

from typing import Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.workflow.dtos import (
    CreateWorkflowDefinitionDTO,
    WorkflowDefinitionResponseDTO,
    TriggerWorkflowDTO,
    WorkflowExecutionResponseDTO,
    CreateAgentDTO,
    ExecuteAgentTaskDTO,
    AgentTaskResultDTO,
)


class IWorkflowEngineService(Protocol):
    async def create_definition(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateWorkflowDefinitionDTO
    ) -> ServiceResult[WorkflowDefinitionResponseDTO]: ...

    async def execute_workflow(
        self, ctx: ServiceContext, dto: TriggerWorkflowDTO
    ) -> ServiceResult[WorkflowExecutionResponseDTO]: ...


class IAgentExecutorService(Protocol):
    async def execute_task(
        self, ctx: ServiceContext, dto: ExecuteAgentTaskDTO
    ) -> ServiceResult[AgentTaskResultDTO]: ...
