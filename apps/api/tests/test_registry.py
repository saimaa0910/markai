import pytest
from unittest.mock import MagicMock
from api.ai.agents.base.registry import AgentRegistry, map_category_to_agent_type
from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.base.manifest import AgentManifest
from api.models.agent import AgentDefinition, AgentStatus, AgentType
from api.models.organization import Organization

@pytest.fixture(autouse=True)
def cleanup_registry():
    # Reset registry state between tests
    AgentRegistry._registry = {}
    AgentRegistry._initialized = False
    yield

def test_registry_registration_and_get():
    manifest = AgentManifest(
        id="TEST_REG",
        name="Registry Test Agent",
        description="Testing registry",
        category="MARKETING",
        metadata={
            "icon": "🤖",
            "gradient": "",
            "accent_color": "",
            "category": "MARKETING",
            "description": "Testing registry"
        }
    )
    agent = BaseMarketingAgent(manifest=manifest)
    
    AgentRegistry.register(agent)
    assert AgentRegistry.get("TEST_REG") == agent
    assert len(AgentRegistry.list()) == 1

def test_registry_sync_to_db():
    manifest = AgentManifest(
        id="TEST_SYNC",
        name="Sync Test Agent",
        description="Testing sync",
        category="CONTENT",
        permissions={"allowed_tools": ["knowledge_tool"]},
        metadata={
            "icon": "🤖",
            "gradient": "",
            "accent_color": "",
            "category": "CONTENT",
            "description": "Testing sync"
        }
    )
    agent = BaseMarketingAgent(manifest=manifest)
    AgentRegistry.register(agent)

    mock_db = MagicMock()
    mock_org = MagicMock(spec=Organization)
    mock_org.id = "mock-org-id"
    mock_org.slug = "mock-org"
    mock_db.query.return_value.all.return_value = [mock_org]
    
    # Configure DB query filter mockup for existing agent (none exists initially)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    AgentRegistry.sync_to_db(mock_db)
    
    # Assert definition was added
    mock_db.add.assert_called_once()
    added_def = mock_db.add.call_args[0][0]
    assert isinstance(added_def, AgentDefinition)
    assert added_def.name == "Sync Test Agent"
    assert added_def.agent_type == AgentType.CONTENT
