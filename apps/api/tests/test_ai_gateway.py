import json
import uuid
from fastapi.testclient import TestClient
from api.main import app
from api.models.membership import UserOrganization, UserRole
from api.models.user import User

client = TestClient(app)


def test_ai_gateway_endpoints():
    # 1. Register and Login to get headers
    email = "aigateway@example.com"
    password = "superpassword123"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "AI Admin",
        "password": password,
        "org_name": "AI Gateway Org"
    })
    
    login_res = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get organization ID
    orgs_res = client.get("/api/v1/organizations/", headers=headers)
    assert orgs_res.status_code == 200
    orgs = orgs_res.json()
    org_id = orgs[0]["id"]
    headers["X-Organization-ID"] = str(org_id)

    # 2. Test GET providers
    res = client.get("/api/v1/ai/providers/", headers=headers)
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 5
    
    groq_prov = next(p for p in providers if p["name"] == "groq")
    assert groq_prov is not None

    # 3. Test GET provider health
    res = client.get(f"/api/v1/ai/providers/{groq_prov['id']}/health", headers=headers)
    assert res.status_code == 200
    health = res.json()
    assert health["provider_name"] == "groq"
    assert "is_healthy" in health

    # 4. Test POST models sync
    res = client.post("/api/v1/ai/models/sync", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 5. Test GET models
    res = client.get("/api/v1/ai/models/", headers=headers)
    assert res.status_code == 200
    models = res.json()
    assert len(models) > 0

    # 6. Test PUT model update
    model_id = models[0]["id"]
    res = client.put(f"/api/v1/ai/models/{model_id}?is_active=false", headers=headers)
    assert res.status_code == 200

    # 7. Test POST playground chat
    res = client.post("/api/v1/ai/playground/chat", json={
        "messages": [{"role": "user", "content": "ping"}],
        "model_name": "llama3-8b-8192",
        "temperature": 0.7
    }, headers=headers)
    assert res.status_code == 200
    chat_res = res.json()
    assert "output" in chat_res
    assert chat_res["model"] == "llama3-8b-8192"

    # 8. Test POST playground stream
    res = client.post("/api/v1/ai/playground/stream", json={
        "messages": [{"role": "user", "content": "ping"}],
        "model_name": "llama3-8b-8192",
        "temperature": 0.7
    }, headers=headers)
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    # 9. Test GET playground history
    res = client.get("/api/v1/ai/playground/history", headers=headers)
    assert res.status_code == 200
    history = res.json()
    assert len(history) > 0

    # 10. Test POST compare
    res = client.post("/api/v1/ai/compare/", json={
        "prompt": "ping",
        "model_names": ["llama3-8b-8192", "llama3-70b-8192"]
    }, headers=headers)
    assert res.status_code == 200
    compare_res = res.json()
    assert len(compare_res["results"]) == 2

    # 11. Test GET analytics
    res = client.get("/api/v1/ai/analytics/", headers=headers)
    assert res.status_code == 200
    analytics = res.json()
    assert "kpis" in analytics
    assert "usages" in analytics
