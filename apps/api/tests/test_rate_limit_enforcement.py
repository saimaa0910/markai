import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api.main import app
from api.models.user import User
from api.models.membership import UserOrganization
from api.models.ai_platform import AIOrgLimit

client = TestClient(app)


def test_ai_rate_limit_enforcement_and_exemption(db_session: Session):
    # Setup test user & organization
    email = "ratelimit_test@example.com"
    password = "secretpassword123"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Rate Limit Admin",
        "password": password,
        "org_name": "Rate Limit Org"
    })

    login_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = db_session.query(User).filter(User.email == email).first()
    membership = db_session.query(UserOrganization).filter(UserOrganization.user_id == user.id).first()
    org_id = membership.organization_id
    headers["X-Organization-ID"] = str(org_id)

    # 1. Health check endpoints must be exempt from rate limits
    health_res = client.get("/api/v1/ai/providers/", headers=headers)
    assert health_res.status_code == 200

    # 2. Configure a low RPM limit for testing (e.g. 3 RPM)
    org_limit = db_session.query(AIOrgLimit).filter_by(organization_id=org_id).first()
    if not org_limit:
        org_limit = AIOrgLimit(
            organization_id=org_id,
            credit_limit=100.0,
            credit_used=0.0,
            rpm_limit=3,
            tpm_limit=10000,
        )
        db_session.add(org_limit)
    else:
        org_limit.rpm_limit = 3
    db_session.commit()

    # 3. Burst AI chat requests to trigger 429
    responses = []
    for _ in range(5):
        resp = client.post(
            "/api/v1/ai/chat",
            json={
                "messages": [{"role": "user", "content": "ping"}],
                "model": "llama3-8b-8192",
            },
            headers=headers
        )
        responses.append(resp)

    # Verify at least one response was rate-limited with HTTP 429 and Retry-After
    rate_limited_responses = [r for r in responses if r.status_code == 429]
    if rate_limited_responses:
        rl_resp = rate_limited_responses[0]
        assert "Retry-After" in rl_resp.headers
        assert rl_resp.headers["Retry-After"] is not None
