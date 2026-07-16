import json
import uuid
from fastapi.testclient import TestClient
from api.main import app
from api.models.membership import UserOrganization, UserRole
from api.models.user import User

client = TestClient(app)


def test_observability_endpoints():
    # 1. Register and Login to get headers and active organization id
    email = "observability@example.com"
    password = "superpassword123"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Observability Admin",
        "password": password,
        "org_name": "Observability Org"
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
    org_id = orgs_res.json()[0]["id"]
    headers["X-Organization-ID"] = str(org_id)

    # 2. Test public Prometheus metrics endpoint
    metrics_res = client.get("/api/v1/observability/metrics")
    assert metrics_res.status_code == 200
    assert "text/plain" in metrics_res.headers["content-type"]
    assert "ai_requests_total" in metrics_res.text

    # 3. Test public detailed health status endpoint
    health_res = client.get("/api/v1/observability/health")
    assert health_res.status_code == 200
    health = health_res.json()
    assert health["status"] in ["healthy", "warning", "critical"]
    assert "database" in health["components"]
    assert "redis" in health["components"]
    assert "workers" in health["components"]

    # 4. Trigger an AI request to verify trace generation and headers injection
    headers["X-Correlation-ID"] = "test-correlation-1234"
    chat_res = client.post("/api/v1/ai/playground/chat", json={
        "messages": [{"role": "user", "content": "hello observability"}],
        "model_name": "llama3-8b-8192",
        "temperature": 0.7
    }, headers=headers)
    assert chat_res.status_code == 200
    
    # Check headers propagation
    assert "x-correlation-id" in chat_res.headers
    assert chat_res.headers["x-correlation-id"] == "test-correlation-1234"
    assert "x-request-id" in chat_res.headers
    # x-trace-id is optional in HTTP headers depending on the exact OTel context propagation in test client
    if "x-trace-id" in chat_res.headers:
        assert len(chat_res.headers["x-trace-id"]) > 0

    # 5. Query traces endpoint and verify our trace span is recorded
    traces_res = client.get("/api/v1/observability/traces", headers=headers)
    assert traces_res.status_code == 200
    traces = traces_res.json()
    assert len(traces) > 0
    # The trace name should match our gateway span name format
    assert any("gateway" in t["name"] for t in traces)

    # 6. Query logs endpoint and verify our request log is recorded
    logs_res = client.get("/api/v1/observability/logs", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) > 0
    # There should be logs logged under the database logging middleware and gateway coordinator
    assert any("HTTP POST" in l["message"] or "AI Request" in l["message"] for l in logs)

    # 7. Query performance analytics endpoint
    perf_res = client.get("/api/v1/observability/performance?days=7", headers=headers)
    assert perf_res.status_code == 200
    perf = perf_res.json()
    assert "summary" in perf
    assert "total_traces" in perf["summary"]
    assert "p90_ms" in perf["summary"]
    assert "provider_comparison" in perf

    # 8. Query live status feed
    live_res = client.get("/api/v1/observability/live", headers=headers)
    assert live_res.status_code == 200
    live = live_res.json()
    assert "traffic_5m" in live
    assert "redis" in live
    assert "workers" in live
    assert "queues" in live

    # 9. Test simulated alert dispatch mutation
    alert_test_res = client.post("/api/v1/observability/alerts/test?severity=warning", headers=headers)
    assert alert_test_res.status_code == 200
    alert_test = alert_test_res.json()
    assert alert_test["success"] is True
    assert alert_test["status"] in ["sent", "failed"]  # sent if mockSMTP/slack succeeded, failed if not but still logs
    assert "channels" in alert_test

    # 10. Query alerts list to verify the test alert record exists
    alerts_res = client.get("/api/v1/observability/alerts", headers=headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) > 0
    assert any(a["alert_type"] == "TEST_ALERT_TRIGGER" for a in alerts)
