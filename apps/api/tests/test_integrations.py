import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.core.security import get_password_hash
from api.models.integration import Integration, IntegrationProvider, IntegrationStatus

client = TestClient(app)


@pytest.fixture
def test_setup(db_session):
    # Create Organization
    org = Organization(name="Test Integration Org", slug="test-int-org")
    db_session.add(org)
    db_session.flush()

    # Create User
    user = User(
        email="int_user@viptant.ai",
        hashed_password=get_password_hash("password"),
        full_name="Integration User",
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


def test_integration_endpoints(db_session, test_setup):
    headers = get_auth_headers(db_session, test_setup["user"])
    headers["X-Organization-ID"] = str(test_setup["org"].id)

    # 1. Fetch OAuth URL
    response = client.get(
        "/api/v1/integrations/oauth/url?provider=GOOGLE_DRIVE",
        headers=headers,
    )
    assert response.status_code == 200
    assert "url" in response.json()

    # 2. Connect Integration
    response = client.post(
        "/api/v1/integrations/",
        headers=headers,
        json={
            "provider": "GOOGLE_DRIVE",
            "name": "Internal Drive Repository",
            "config": {"folder_id": "root-folder"},
        },
    )
    assert response.status_code == 201
    int_data = response.json()
    assert int_data["status"] == "CONNECTED"
    int_id = int_data["id"]

    # 3. List integrations
    response = client.get("/api/v1/integrations/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

    # 4. Trigger Sync
    response = client.post(
        f"/api/v1/integrations/{int_id}/sync",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 5. Get sync jobs
    response = client.get(
        f"/api/v1/integrations/{int_id}/sync-jobs",
        headers=headers,
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
