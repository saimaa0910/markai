import pytest
from unittest.mock import MagicMock, patch
from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.exceptions import PolicyValidationError, PermissionValidationError
from api.models.agent import AgentSession, AgentDefinition

@pytest.fixture
def manifest():
    return AgentManifest(
        id="TEST_BASE",
        name="Base Agent",
        description="Testing base",
        category="MARKETING",
        default_model="gemini-1.5-flash",
        policies={
            "allowed_models": ["gemini-1.5-flash"],
            "allowed_providers": ["google"]
        },
        permissions={
            "allowed_tools": ["knowledge_tool"]
        },
        metadata={
            "icon": "🤖",
            "gradient": "",
            "accent_color": "",
            "category": "MARKETING",
            "description": "Testing base"
        }
    )

def test_base_marketing_agent_invalid_model(manifest):
    agent = BaseMarketingAgent(manifest=manifest)
    db = MagicMock()
    session = MagicMock(spec=AgentSession)
    session.agent = MagicMock(spec=AgentDefinition)
    session.agent.preferred_model = "gpt-4o"  # Not allowed in manifest!
    session.agent.preferred_provider = "google"
    session.agent.allowed_tools = ["knowledge_tool"]

    with pytest.raises(PolicyValidationError) as excinfo:
        agent.execute(db, session, "hello")
    assert "not permitted by agent policies" in str(excinfo.value)

def test_base_marketing_agent_invalid_tool(manifest):
    agent = BaseMarketingAgent(manifest=manifest)
    db = MagicMock()
    session = MagicMock(spec=AgentSession)
    session.agent = MagicMock(spec=AgentDefinition)
    session.agent.preferred_model = "gemini-1.5-flash"
    session.agent.preferred_provider = "google"
    session.agent.allowed_tools = ["email_tool"]  # Not allowed in manifest!

    with pytest.raises(PermissionValidationError) as excinfo:
        agent.execute(db, session, "hello")
    assert "not authorized by agent permissions" in str(excinfo.value)

@patch("api.ai.runtime.agent_runtime.agent_runtime.execute")
def test_base_marketing_agent_successful_dispatch(mock_execute, manifest):
    agent = BaseMarketingAgent(manifest=manifest)
    db = MagicMock()
    session = MagicMock(spec=AgentSession)
    session.agent = MagicMock(spec=AgentDefinition)
    session.agent.preferred_model = "gemini-1.5-flash"
    session.agent.preferred_provider = "google"
    session.agent.allowed_tools = ["knowledge_tool"]

    agent.execute(db, session, "hello")
    mock_execute.assert_called_once()
