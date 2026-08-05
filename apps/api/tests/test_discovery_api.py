import pytest
from fastapi.testclient import TestClient
from api.main import app
from tests.test_agents import test_setup, get_auth_headers

client = TestClient(app)

def test_discovery_agents_list(db_session, test_setup):
    headers = get_auth_headers(db_session, test_setup["user"])
    headers["X-Organization-ID"] = str(test_setup["org"].id)

    response = client.get("/api/v1/agents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # We should have registered Content agent and placeholders
    ids = [agent["id"] for agent in data]
    assert "CONTENT" in ids
    assert "SEO" in ids
    assert "RESEARCH" in ids
    
    # Check key structure of first agent
    first_agent = data[0]
    assert "id" in first_agent
    assert "name" in first_agent
    assert "capabilities" in first_agent
    assert "streaming_support" in first_agent
    assert "metadata" in first_agent
