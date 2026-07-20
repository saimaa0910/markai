import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api.main import app
from api.models.agent import AgentDefinition, AgentSession, AgentType
from api.models.membership import UserOrganization
from api.models.workflow import WorkflowDefinition
from api.ai.tools import ToolInput
from api.ai.tools.workflow_tool import WorkflowTool

client = TestClient(app)


@pytest.fixture
def auth_headers(db_session: Session):
    email = f"agent_tester_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword",
            "full_name": "Agent Tester",
            "org_name": "Agent Organization",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "strongpassword"},
    ).json()
    token = login["access_token"]

    # Retrieve Org details
    orgs = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    org_id = orgs[0]["id"]
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}


def test_list_agent_templates(auth_headers):
    # Verify templates endpoint is accessible and returns the 3 default templates
    res = client.get("/api/v1/agents/templates", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    names = [tmpl["name"] for tmpl in data]
    assert "Content Agent" in names
    assert "SEO Agent" in names
    assert "Campaign Agent" in names


def test_agent_favorite_and_pin(auth_headers, db_session: Session):
    org_id = uuid.UUID(auth_headers["X-Organization-ID"])
    
    agent = AgentDefinition(
        name="Test Control Agent",
        agent_type=AgentType.CUSTOM,
        organization_id=org_id,
        allowed_tools=[],
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    # 1. Favorite Toggle
    res = client.patch(f"/api/v1/agents/definitions/{agent.id}/favorite", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["is_favorite"] is True

    # 2. Pin Toggle
    res = client.patch(f"/api/v1/agents/definitions/{agent.id}/pin", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["is_pinned"] is True

    # 3. Archive
    res = client.patch(f"/api/v1/agents/definitions/{agent.id}/archive", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ARCHIVED"

    # 4. Restore
    res = client.patch(f"/api/v1/agents/definitions/{agent.id}/restore", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ACTIVE"


def test_agent_duplicate(auth_headers, db_session: Session):
    org_id = uuid.UUID(auth_headers["X-Organization-ID"])
    
    agent = AgentDefinition(
        name="Original Agent",
        agent_type=AgentType.RESEARCH,
        organization_id=org_id,
        allowed_tools=["crm_tool"],
        preferred_model="gemini-2.5-pro",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    res = client.post(f"/api/v1/agents/definitions/{agent.id}/duplicate", headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Original Agent (Copy)"
    assert data["preferred_model"] == "gemini-2.5-pro"
    assert "crm_tool" in data["allowed_tools"]


def test_export_import_agent(auth_headers, db_session: Session):
    org_id = uuid.UUID(auth_headers["X-Organization-ID"])
    
    agent = AgentDefinition(
        name="Exportable Agent",
        agent_type=AgentType.ANALYTICS,
        organization_id=org_id,
        allowed_tools=["campaign_tool"],
        preferred_model="gemini-2.5-flash",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    # Export
    res_export = client.get(f"/api/v1/agents/definitions/{agent.id}/export", headers=auth_headers)
    assert res_export.status_code == 200
    blueprint = res_export.json()
    assert blueprint["name"] == "Exportable Agent"
    assert blueprint["agent_type"] == "ANALYTICS"

    # Import
    blueprint["name"] = "Imported Brand Agent"
    res_import = client.post("/api/v1/agents/definitions/import", json=blueprint, headers=auth_headers)
    assert res_import.status_code == 201
    imported_data = res_import.json()
    assert imported_data["name"] == "Imported Brand Agent"
    assert imported_data["agent_type"] == "ANALYTICS"
    assert "campaign_tool" in imported_data["allowed_tools"]


def test_agent_memory_endpoints(auth_headers, db_session: Session):
    org_id = uuid.UUID(auth_headers["X-Organization-ID"])
    
    agent = AgentDefinition(
        name="Memory Test Agent",
        agent_type=AgentType.CUSTOM,
        organization_id=org_id,
        allowed_tools=[],
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    # 1. Agent long term memory write
    res_lt = client.post(
        f"/api/v1/memory/agents/{agent.id}?key=user_preference&value=dark_mode",
        headers=auth_headers
    )
    assert res_lt.status_code == 201
    
    # Read long term memory
    res_lt_read = client.get(f"/api/v1/memory/agents/{agent.id}", headers=auth_headers)
    assert res_lt_read.status_code == 200
    assert len(res_lt_read.json()) > 0
    assert res_lt_read.json()[0]["memory_key"] == "user_preference"
    assert res_lt_read.json()[0]["memory_value"] == "dark_mode"

    # Retrieve current user id
    uo = db_session.query(UserOrganization).filter(UserOrganization.organization_id == org_id).first()
    assert uo is not None

    # Create session
    session = AgentSession(
        agent_id=agent.id,
        organization_id=org_id,
        user_id=uo.user_id,
        title="Active Chat"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # 2. Session short term memory write
    res_st = client.post(
        f"/api/v1/memory/sessions/{session.id}?key=last_action&value=clicked_export",
        headers=auth_headers
    )
    assert res_st.status_code == 201

    # Read session short term memory
    res_st_read = client.get(f"/api/v1/memory/sessions/{session.id}", headers=auth_headers)
    assert res_st_read.status_code == 200
    assert len(res_st_read.json()) > 0
    assert res_st_read.json()[0]["memory_key"] == "last_action"
    assert res_st_read.json()[0]["memory_value"] == "clicked_export"


def test_workflow_tool_execution(auth_headers, db_session: Session):
    org_id = uuid.UUID(auth_headers["X-Organization-ID"])
    uo = db_session.query(UserOrganization).filter(UserOrganization.organization_id == org_id).first()
    assert uo is not None
    
    # Create mock workflow definition
    wf = WorkflowDefinition(
        name="Test Workflow for Agent Tool",
        organization_id=org_id,
        steps_definition={"steps": []},
    )
    db_session.add(wf)
    db_session.commit()
    db_session.refresh(wf)

    tool = WorkflowTool()
    assert tool.name == "workflow_tool"
    assert "workflow_id" in tool.parameters_schema["required"]

    # Test tool execution with non-existent ID
    bad_input = ToolInput(
        tool_name="workflow_tool",
        params={"workflow_id": str(uuid.uuid4())},
        organization_id=str(org_id),
        user_id=str(uo.user_id),
    )
    res_bad = tool.execute(bad_input, db_session)
    assert res_bad.success is False
    assert "not found" in res_bad.error

    # Test tool execution with real ID, queuing asynchronously
    good_input = ToolInput(
        tool_name="workflow_tool",
        params={"workflow_id": str(wf.id), "wait_for_completion": False},
        organization_id=str(org_id),
        user_id=str(uo.user_id),
    )
    res_good = tool.execute(good_input, db_session)
    assert res_good.success is True
    assert res_good.output["status"] == "QUEUED"
