"""
EAIMOS AI Agent Platform Repository Module — Sprint 6
=====================================================
Repository implementations for AI Agent Platform models:
AgentDefinition, AgentSession, AgentRun, AgentLog, AgentTool, AgentMemory.
"""

from typing import Any, List, Optional
import uuid

from api.models.agent import (
    AgentDefinition,
    AgentSession,
    AgentRun,
    AgentLog,
)
from api.models.agent_tools import AgentTool, AgentToolExecution
from api.models.memory import AgentMemory
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class EnterpriseAgentDefinitionRepository(TenantRepository[AgentDefinition]):
    """Data access layer for Agent Definitions."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AgentDefinition, organization_id=organization_id)

    async def get_by_name(self, session: Any, name: str) -> Optional[AgentDefinition]:
        filters = [FilterParam(field="name", operator=FilterOperator.EQ, value=name)]
        return await self.find_one(session=session, filters=filters)


class AgentSessionRepository(TenantRepository[AgentSession]):
    """Data access layer for active agent execution sessions."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AgentSession, organization_id=organization_id)


class AgentRunRepository(TenantRepository[AgentRun]):
    """Data access layer for agent execution runs."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AgentRun, organization_id=organization_id)

    async def list_by_agent(self, session: Any, agent_id: uuid.UUID) -> List[AgentRun]:
        filters = [FilterParam(field="agent_id", operator=FilterOperator.EQ, value=agent_id)]
        return await self.find_many(session=session, filters=filters)


class AgentToolRepository(TenantRepository[AgentTool]):
    """Data access layer for registered agent tools."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AgentTool, organization_id=organization_id)


class AgentMemoryRepository(TenantRepository[AgentMemory]):
    """Data access layer for long-term agent memories."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AgentMemory, organization_id=organization_id)
