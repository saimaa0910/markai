import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from api.models.user import User
from api.models.membership import UserOrganization, UserRole
from api.models.ai_platform import AIProvider, AIProviderKey, AIProviderHealth, AIOrgLimit
from api.ai.gateway.coordinator import AIGateway
from api.ai.registry.manager import ModelRegistryManager

client = TestClient(app)


def test_ai_gateway_limits_and_endpoints(db_session: Session):
    # 1. Setup mock user, organization, and auth headers
    email = "limitstest@example.com"
    password = "secretpassword123"
    
    # Register user
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Limits Admin",
        "password": password,
        "org_name": "Limits Test Org"
    })

    # Log in
    login_res = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Extract user and org details
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    membership = db_session.query(UserOrganization).filter(UserOrganization.user_id == user.id).first()
    org_id = membership.organization_id
    headers["X-Organization-ID"] = str(org_id)

    # Seed default models
    ModelRegistryManager.seed_default_models(db_session)
    
    # Verify AIOrgLimit is automatically seeded or fetch it
    gateway = AIGateway()
    gateway._check_and_seed_limit(db_session, org_id)
    
    limit_rec = db_session.query(AIOrgLimit).filter_by(organization_id=org_id).first()
    assert limit_rec is not None
    assert float(limit_rec.credit_limit) == 100.00
    assert float(limit_rec.credit_used) == 0.0

    # 2. Test execution cost update
    # Call chat and assert cost tracking increments credit_used
    res = gateway.chat(
        db=db_session,
        messages=[{"role": "user", "content": "ping"}],
        organization_id=org_id,
        user_id=user.id,
        model_name="llama3-8b-8192",
    )
    assert "content" in res
    
    db_session.refresh(limit_rec)
    assert float(limit_rec.credit_used) > 0.0

    # 3. Test budget limit enforcement
    # Update credit_limit to be smaller than credit_used
    limit_rec.credit_limit = 0.0001
    db_session.commit()
    
    with pytest.raises(RuntimeError) as exc_info:
        gateway.chat(
            db=db_session,
            messages=[{"role": "user", "content": "ping"}],
            organization_id=org_id,
            user_id=user.id,
            model_name="llama3-8b-8192",
        )
    assert "exceeded its allocated AI credit" in str(exc_info.value)

    # Reset credit limit to test endpoints
    limit_rec.credit_limit = 500.0
    db_session.commit()

    # 4. Test GET/POST provider keys endpoints
    # Get provider list to fetch an ID
    prov_res = client.get("/api/v1/ai/providers/", headers=headers)
    assert prov_res.status_code == 200
    providers_list = prov_res.json()
    assert len(providers_list) > 0
    groq_prov = next(p for p in providers_list if p["name"] == "groq")
    groq_id = groq_prov["id"]

    # Post new key configuration
    key_payload = {
        "provider_id": groq_id,
        "api_key": "gsk_testkeyrotate1234567890",
        "is_active": True
    }
    post_key_res = client.post("/api/v1/ai/providers/keys/", json=key_payload, headers=headers)
    assert post_key_res.status_code == 200
    key_data = post_key_res.json()
    assert key_data["provider_name"] == "groq"
    assert "gsk_tes" in key_data["masked_key"]
    key_record_id = key_data["id"]

    # List keys
    list_keys_res = client.get("/api/v1/ai/providers/keys/", headers=headers)
    assert list_keys_res.status_code == 200
    assert len(list_keys_res.json()) == 1

    # Rotate key
    rotate_payload = {"api_key": "gsk_rotatedkeyvalue987654321"}
    rotate_res = client.post(f"/api/v1/ai/providers/keys/{key_record_id}/rotate", json=rotate_payload, headers=headers)
    assert rotate_res.status_code == 200
    assert "gsk_rot" in rotate_res.json()["masked_key"]

    # 5. Test health pings & incidents
    # Seed an unhealthy check directly to DB to trigger an incident
    unhealthy_ping = AIProviderHealth(
        provider_id=uuid.UUID(groq_id),
        latency=450,
        is_healthy=False,
        error_message="HTTP 503 Service Unavailable"
    )
    db_session.add(unhealthy_ping)
    db_session.commit()

    # Get active incidents
    incidents_res = client.get("/api/v1/ai/providers/health/incidents", headers=headers)
    assert incidents_res.status_code == 200
    incidents = incidents_res.json()
    assert len(incidents) > 0
    target_incident = next(i for i in incidents if i["provider"] == "groq" and i["resolved"] is False)
    assert "HTTP 503" in target_incident["message"]

    # Resolve incident
    resolve_res = client.post(f"/api/v1/ai/providers/health/incidents/{target_incident['id']}/resolve", headers=headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["success"] is True

    # Check incident resolved status
    resolved_check = db_session.query(AIProviderHealth).filter_by(id=uuid.UUID(target_incident["id"])).first()
    assert resolved_check.is_healthy is True

    # 6. Test credit limits endpoints
    # Get current limit
    curr_limit_res = client.get("/api/v1/ai/providers/limits/current", headers=headers)
    assert curr_limit_res.status_code == 200
    assert curr_limit_res.json()["credit_limit"] == 500.0

    # Add credits
    add_credits_res = client.post(f"/api/v1/ai/providers/limits/{org_id}/credits", json={"amount": 150.0}, headers=headers)
    assert add_credits_res.status_code == 200
    assert add_credits_res.json()["credit_limit"] == 650.0

    # Modify limits constraints
    update_limits_res = client.post(f"/api/v1/ai/providers/limits/{org_id}/limits", json={"rpm_limit": 120, "tpm_limit": 75000}, headers=headers)
    assert update_limits_res.status_code == 200
    updated = update_limits_res.json()
    assert updated["rpm_limit"] == 120
    assert updated["tpm_limit"] == 75000
