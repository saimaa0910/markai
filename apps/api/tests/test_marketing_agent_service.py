import pytest
from unittest.mock import MagicMock, patch
import uuid
from api.services.marketing_agent_service import MarketingAgentService
from api.models.agent import AgentSession, AgentDefinition, AgentType
from api.models.organization import Organization
from api.models.user import User
from api.ai.agents.base.registry import AgentRegistry

@pytest.fixture(autouse=True)
def setup_registries():
    AgentRegistry.initialize()
    yield

@patch("api.ai.agents.seo.agent.SEOAgent.execute")
def test_execute_marketing_agent_service(mock_execute, db_session):
    # 1. Create Organization
    org = Organization(name="Test Service Org", slug="test-service-org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    
    # 2. Create User
    user = User(
        email="test_service_user@viptant.ai",
        hashed_password="password",
        full_name="Test Service User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    org_id = org.id
    user_id = user.id
    
    # 3. Create AgentDefinition referencing organization
    db_def = AgentDefinition(
        organization_id=org_id,
        name="SEO Agent",
        agent_type=AgentType.SEO,
        status="ACTIVE",
        system_prompt="system",
        allowed_tools=["knowledge_tool"],
    )
    db_session.add(db_def)
    db_session.commit()
    db_session.refresh(db_def)
    
    mock_execute.return_value = {"status": "success", "content": "seo results"}
    
    result = MarketingAgentService.execute_agent(
        db=db_session,
        organization_id=org_id,
        user_id=user_id,
        agent_id="SEO",
        user_input="optimize home page"
    )
    
    assert "session_id" in result
    assert result["result"] == {"status": "success", "content": "seo results"}
    mock_execute.assert_called_once()
