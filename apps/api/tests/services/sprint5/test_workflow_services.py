"""
Sprint 5 Workflows, Agents & Integrations Service Tests
==========================================================
Tests for WorkflowEngineService, AgentExecutorService, and IntegrationService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.workflow.workflow_engine_service import WorkflowEngineService
from api.services.workflow.agent_executor_service import AgentExecutorService
from api.services.workflow.integration_service import IntegrationService
from api.services.workflow.dtos import (
    CreateWorkflowDefinitionDTO,
    TriggerWorkflowDTO,
    ExecuteAgentTaskDTO,
    RegisterWebhookDTO,
)


def make_ctx() -> ServiceContext:
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.uuid4()
    ctx.organization_id = uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.is_tenant_member.return_value = True
    return ctx


def make_authorizer() -> MagicMock:
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.return_value = None
    auth.check_permission.return_value = True
    return auth


def make_uow() -> MagicMock:
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = MagicMock()
    uow.add_event = MagicMock()
    return uow


def make_entity(**kwargs) -> MagicMock:
    entity = MagicMock()
    entity.id = kwargs.get("id", uuid.uuid4())
    entity.created_at = datetime.now(timezone.utc)
    for k, v in kwargs.items():
        setattr(entity, k, v)
    return entity


class TestWorkflowEngineService:
    @pytest.mark.asyncio
    async def test_create_workflow_definition(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        wf_entity = make_entity(
            organization_id=ctx.organization_id,
            name="Lead Qualification Workflow",
            description="Qualify leads automatically",
            status="DRAFT",
            trigger="MANUAL",
            steps_definition=[{"id": "s1", "type": "agent_run"}],
            cron_expression=None,
            max_retries=3,
            timeout_seconds=3600,
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = wf_entity
        uow.get_repository.return_value = repo_mock

        svc = WorkflowEngineService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.workflow.workflow_engine_service._WorkflowDefinitionRepository", return_value=repo_mock):
            res = await svc.create_definition(
                ctx,
                org_id=ctx.organization_id,
                dto=CreateWorkflowDefinitionDTO(
                    name="Lead Qualification Workflow",
                    trigger="MANUAL",
                    steps_definition=[{"id": "s1", "type": "agent_run"}],
                ),
            )

        assert res.is_success
        assert res.data.name == "Lead Qualification Workflow"

    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = WorkflowEngineService(authorizer=authorizer)
        res = await svc.execute_workflow(
            ctx,
            dto=TriggerWorkflowDTO(
                workflow_id=uuid.uuid4(),
                inputs={"lead_id": "123"},
            ),
        )

        assert res.is_success
        assert res.data.status == "COMPLETED"


class TestAgentExecutorService:
    @pytest.mark.asyncio
    async def test_execute_agent_task(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = AgentExecutorService(authorizer=authorizer)
        res = await svc.execute_task(
            ctx,
            dto=ExecuteAgentTaskDTO(
                agent_id=uuid.uuid4(),
                task_instructions="Analyze market trends for Q4",
            ),
        )

        assert res.is_success
        assert res.data.status == "COMPLETED"
        assert len(res.data.tool_calls_made) == 1


class TestIntegrationService:
    @pytest.mark.asyncio
    async def test_register_webhook(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = IntegrationService(authorizer=authorizer)
        res = await svc.register_webhook(
            ctx,
            org_id=ctx.organization_id,
            dto=RegisterWebhookDTO(
                name="HubSpot Sync Webhook",
                target_url="https://api.hubspot.com/webhook",
                events=["workflow.execution_completed"],
            ),
        )

        assert res.is_success
        assert res.data["name"] == "HubSpot Sync Webhook"
