"""
EAIMOS Workflow Dependencies
==============================
FastAPI dependency providers for Sprint 5 Workflow services.
"""

from api.services.base.dependency_provider import container
from api.services.workflow.workflow_engine_service import WorkflowEngineService
from api.services.workflow.agent_executor_service import AgentExecutorService
from api.services.workflow.integration_service import IntegrationService


def get_workflow_engine_service() -> WorkflowEngineService:
    return WorkflowEngineService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_agent_executor_service() -> AgentExecutorService:
    return AgentExecutorService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_integration_service() -> IntegrationService:
    return IntegrationService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
