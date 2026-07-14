import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.core.security import get_password_hash
from api.models.integration import Notification, NotificationChannel, NotificationPriority

client = TestClient(app)


@pytest.fixture
def test_setup(db_session):
    # Create Organization
    org = Organization(name="Test Notif Org", slug="test-notif-org")
    db_session.add(org)
    db_session.flush()

    # Create User
    user = User(
        email="notif_user@viptant.ai",
        hashed_password=get_password_hash("password"),
        full_name="Notification User",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Bind membership
    member = UserOrganization(
        user_id=user.id,
        organization_id=org.id,
        role=UserRole.MEMBER,
    )
    db_session.add(member)
    db_session.commit()

    return {"org": org, "user": user, "member": member}


def get_auth_headers(db_session, user):
    from api.core.security import create_access_token
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


def test_notification_endpoints(db_session, test_setup):
    headers = get_auth_headers(db_session, test_setup["user"])
    headers["X-Organization-ID"] = str(test_setup["org"].id)

    # 1. Seed Notification
    notif = Notification(
        user_id=test_setup["user"].id,
        organization_id=test_setup["org"].id,
        title="Weekly Analytics Report",
        body="Your analytics report is ready.",
        channel=NotificationChannel.IN_APP,
        priority=NotificationPriority.MEDIUM,
        is_read=False,
    )
    db_session.add(notif)
    db_session.commit()

    # 2. List Notifications
    response = client.get("/api/v1/notifications/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["title"] == "Weekly Analytics Report"

    # 3. Mark Read
    response = client.post(
        f"/api/v1/notifications/{notif.id}/read",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["is_read"] is True

    # 4. Get Preferences
    response = client.get("/api/v1/notifications/preferences", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
