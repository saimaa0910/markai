import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.core.security import get_password_hash
from api.models.ai_usage import AITokenUsage

client = TestClient(app)


@pytest.fixture
def test_setup(db_session):
    # Create Organization
    org = Organization(name="Test Analytics Org", slug="test-analytics-org")
    db_session.add(org)
    db_session.flush()

    # Create User
    user = User(
        email="analytics_user@viptant.ai",
        hashed_password=get_password_hash("password"),
        full_name="Analytics User",
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


def test_analytics_endpoints(db_session, test_setup):
    headers = get_auth_headers(db_session, test_setup["user"])
    headers["X-Organization-ID"] = str(test_setup["org"].id)

    # Seed token usage record
    usage = AITokenUsage(
        organization_id=test_setup["org"].id,
        user_id=test_setup["user"].id,
        provider="openai",
        model_name="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        cost_usd=0.03,
        latency_ms=1200,
        status="success",
    )
    db_session.add(usage)
    db_session.commit()

    # 1. Executive dashboard
    response = client.get("/api/v1/analytics/executive", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "ai_platform" in data
    assert data["ai_platform"]["total_tokens_used"] == 1500

    # 2. Token usage trends
    response = client.get("/api/v1/analytics/token-usage", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["tokens_used"] == 1500
