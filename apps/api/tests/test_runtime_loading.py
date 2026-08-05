import pytest
from api.ai.agents.base.registry import AgentRegistry
from api.models.agent import AgentDefinition
from api.models.organization import Organization

def test_dynamic_prompt_compilation(db_session):
    AgentRegistry.initialize()
    
    # Setup test org
    org = Organization(name="Test Refactor Org", slug="test-refactor-org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Sync registries to DB
    AgentRegistry.sync_to_db(db_session)

    # Fetch SEO Agent definition
    seo_def = db_session.query(AgentDefinition).filter(
        AgentDefinition.organization_id == org.id,
        AgentDefinition.name == "SEO Agent"
    ).first()

    assert seo_def is not None
    assert "CAPABILITY: SEO" in seo_def.system_prompt
    assert "Standard enterprise SEO guidelines" in seo_def.system_prompt
