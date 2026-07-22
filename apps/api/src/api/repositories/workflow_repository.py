"""
EAIMOS Workflow Engine Repository Module — Sprint 7
===================================================
Repository implementations for Workflow Engine models:
WorkflowDefinition, WorkflowExecution, WorkflowStep, WorkflowTrigger.
"""

from typing import Any, List, Optional
import uuid

from api.models.workflow import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    WorkflowTrigger,
)
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class WorkflowDefinitionRepository(TenantRepository[WorkflowDefinition]):
    """Data access layer for Workflow Definitions."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(WorkflowDefinition, organization_id=organization_id)

    async def get_by_name(self, session: Any, name: str) -> Optional[WorkflowDefinition]:
        filters = [FilterParam(field="name", operator=FilterOperator.EQ, value=name)]
        return await self.find_one(session=session, filters=filters)


class WorkflowExecutionRepository(TenantRepository[WorkflowExecution]):
    """Data access layer for Workflow Executions."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(WorkflowExecution, organization_id=organization_id)

    async def list_by_workflow(self, session: Any, workflow_id: uuid.UUID) -> List[WorkflowExecution]:
        filters = [FilterParam(field="workflow_id", operator=FilterOperator.EQ, value=workflow_id)]
        return await self.find_many(session=session, filters=filters)


class WorkflowStepRepository(TenantRepository[WorkflowStep]):
    """Data access layer for Workflow Steps."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(WorkflowStep, organization_id=organization_id)


class WorkflowTriggerRepository(TenantRepository[WorkflowTrigger]):
    """Data access layer for Workflow Triggers."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(WorkflowTrigger, organization_id=organization_id)
