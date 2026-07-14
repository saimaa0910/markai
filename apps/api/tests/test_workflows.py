import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.core.security import get_password_hash
from api.models.workflow import WorkflowDefinition, WorkflowExecution, ExecutionStatus, WorkflowTrigger

client = TestClient(app)


@pytest.fixture
def test_setup(db_session):
    # Create Organization
    org = Organization(name="Test Workflow Org", slug="test-wf-org")
    db_session.add(org)
    db_session.flush()

    # Create User
    user = User(
        email="wf_user@viptant.ai",
        hashed_password=get_password_hash("password"),
        full_name="Workflow User",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Bind membership
    member = UserOrganization(
        user_id=user.id,
        organization_id=org.id,
        role=UserRole.OWNER,
    )
    db_session.add(member)
    db_session.commit()

    return {"org": org, "user": user, "member": member}


def get_auth_headers(db_session, user):
    from api.core.security import create_access_token
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


def test_workflow_definition_crud(db_session, test_setup):
    headers = get_auth_headers(db_session, test_setup["user"])
    headers["X-Organization-ID"] = str(test_setup["org"].id)

    # 1. Create Workflow Definition
    response = client.post(
        "/api/v1/workflows/definitions",
        headers=headers,
        json={
            "name": "Nurture Lead Workflow",
            "description": "Sends alert when lead is new",
            "trigger": "MANUAL",
            "steps_definition": [
                {
                    "id": "notify_step",
                    "type": "notify",
                    "params": {"title": "Lead Alert", "body": "A new lead needs attention: {{lead_name}}"},
                }
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Nurture Lead Workflow"
    wf_id = data["id"]

    # 2. Get Definition
    response = client.get(f"/api/v1/workflows/definitions/{wf_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Nurture Lead Workflow"

    # 3. List definitions
    response = client.get("/api/v1/workflows/definitions", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

    # 4. Trigger Execution
    response = client.post(
        f"/api/v1/workflows/definitions/{wf_id}/execute",
        headers=headers,
        json={"input_data": {"lead_name": "Alice Cooper"}},
    )
    assert response.status_code == 201
    exec_data = response.json()
    assert exec_data["status"] == "COMPLETED"
    assert exec_data["workflow_id"] == wf_id
