import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentType, AgentStatus
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.core.security import get_password_hash

client = TestClient(app)


@pytest.fixture
def test_setup(db_session):
    # Create Organization
    org = Organization(name="Test Org", slug="test-org")
    db_session.add(org)
    db_session.flush()

    # Create User
    user = User(
        email="test_user@viptant.ai",
        hashed_password=get_password_hash("password"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Bind membership
    member = UserOrganization(
        user_id=user.id,
        organization_id=org.id,
        role=UserRole.ADMIN,
    )
    db_session.add(member)
    db_session.commit()

    return {"org": org, "user": user, "member": member}


def get_auth_headers(db_session, user):
    from api.core.security import create_access_token
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


def test_agent_definition_crud(db_session, test_setup):
    headers = get_auth_headers(db_session, test_setup["user"])
    headers["X-Organization-ID"] = str(test_setup["org"].id)

    # 1. Create Agent Definition
    response = client.post(
        "/api/v1/agents/definitions",
        headers=headers,
        json={
            "name": "Marketing Specialist",
            "description": "Writes posts and runs campaigns",
            "agent_type": "MARKETING",
            "system_prompt": "You are a professional assistant.",
            "allowed_tools": ["crm_tool"],
            "temperature": 0.5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Marketing Specialist"
    agent_id = data["id"]

    # 2. Get Agent Definition
    response = client.get(f"/api/v1/agents/definitions/{agent_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Marketing Specialist"

    # 3. List definitions
    response = client.get("/api/v1/agents/definitions", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

    # 4. Update Definition
    response = client.patch(
        f"/api/v1/agents/definitions/{agent_id}",
        headers=headers,
        json={"name": "Specialist v2"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Specialist v2"

    # 5. Delete Definition
    response = client.delete(f"/api/v1/agents/definitions/{agent_id}", headers=headers)
    assert response.status_code == 204


def test_agent_session_and_run(db_session, test_setup):
    headers = get_auth_headers(db_session, test_setup["user"])
    headers["X-Organization-ID"] = str(test_setup["org"].id)

    # Create definition
    agent = AgentDefinition(
        name="Test Executor Agent",
        agent_type=AgentType.CUSTOM,
        status=AgentStatus.ACTIVE,
        organization_id=test_setup["org"].id,
        temperature=0.7,
        memory_enabled=True,
    )
    db_session.add(agent)
    db_session.commit()

    # 1. Create Session
    response = client.post(
        "/api/v1/agents/sessions",
        headers=headers,
        json={
            "agent_id": str(agent.id),
            "title": "Conversational Marketing Flow",
        },
    )
    assert response.status_code == 201
    session_id = response.json()["id"]

    # 2. Trigger run (Simulated due to model/credential fallbacks)
    # We test that the run is created, status handles logic correctly
    response = client.post(
        f"/api/v1/agents/sessions/{session_id}/run",
        headers=headers,
        json={"user_input": "Hello agent, find leads."},
    )
    assert response.status_code == 201
    run_data = response.json()
    assert run_data["session_id"] == session_id
    assert run_data["user_input"] == "Hello agent, find leads."
    assert "status" in run_data
