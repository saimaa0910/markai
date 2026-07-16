import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

from api.main import app
from api.models.user import User
from api.models.membership import UserOrganization
from api.models.ai_registry import AIModelRegistry
from api.ai.router.engine import ModelRouter
from api.ai.gateway.coordinator import AIGateway
from api.core.redis_manager import RedisConnectionManager
from api.services.cache_service import CacheService

client = TestClient(app)

class MockRedisClient:
    def __init__(self):
        self.store = {}
    
    def get(self, key):
        return self.store.get(key)
        
    def set(self, key, value, ttl=None):
        self.store[key] = value
        return True

    def setex(self, key, ttl, value):
        self.store[key] = value
        return True


@pytest.fixture(autouse=True)
def patch_redis(monkeypatch):
    mock_client = MockRedisClient()
    monkeypatch.setattr(RedisConnectionManager, "get_client", lambda self: mock_client)
    monkeypatch.setattr(RedisConnectionManager, "connect", lambda self: None)


def test_routing_strategies(db_session: Session):
    router = ModelRouter()
    
    # 1. Test strategy: cheapest
    cheapest_candidates = router.route(db_session, "chat", strategy="cheapest")
    assert len(cheapest_candidates) > 0
    prices = [float(c.input_token_price + c.output_token_price) for c in cheapest_candidates]
    assert prices == sorted(prices)

    # 2. Test strategy: fastest
    fastest_candidates = router.route(db_session, "chat", strategy="fastest")
    assert len(fastest_candidates) > 0
    latencies = [float(c.latency) for c in fastest_candidates]
    assert latencies == sorted(latencies)

    # 3. Test strategy: highest_quality
    quality_candidates = router.route(db_session, "chat", strategy="highest_quality")
    assert len(quality_candidates) > 0
    priorities = [c.priority for c in quality_candidates]
    assert priorities == sorted(priorities, reverse=True)


def test_load_balancer_round_robin():
    router = ModelRouter()
    models = [
        AIModelRegistry(model_name="model-a", provider="openai", context_window=1000),
        AIModelRegistry(model_name="model-b", provider="openai", context_window=1000),
        AIModelRegistry(model_name="model-c", provider="openai", context_window=1000)
    ]
    
    res1 = router._load_balance(models, "round_robin")
    res2 = router._load_balance(models, "round_robin")
    assert res1 != res2


def test_circuit_breaker_blacklist(db_session: Session):
    cache = CacheService()
    # Write using standard CacheService set method
    cache.set("blacklist", "model:gpt-4o-mini", "failed", ttl=300)
    
    router = ModelRouter()
    candidates = router.route(db_session, "chat")
    names = [c.model_name for c in candidates]
    assert "gpt-4o-mini" not in names


def test_router_api_rules_and_simulation(db_session: Session):
    email = "routertest@example.com"
    password = "secretpassword123"
    
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Router Admin",
        "password": password,
        "org_name": "Router Org"
    })

    login_res = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = db_session.query(User).filter(User.email == email).first()
    membership = db_session.query(UserOrganization).filter(UserOrganization.user_id == user.id).first()
    org_id = membership.organization_id
    headers["X-Organization-ID"] = str(org_id)

    # 1. Test get strategies list
    res = client.get("/api/v1/ai/router/strategies", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) > 0

    # 2. Test create routing rule policy
    res = client.post("/api/v1/ai/router/rules", json={
        "name": "Cheapest chat override",
        "scope": "organization",
        "request_type": "chat",
        "routing_strategy": "cheapest",
        "priority": 100,
        "conditions": {"environment": "development"}
    }, headers=headers)
    assert res.status_code == 201
    rule_id = res.json()["id"]

    # 3. Test list rules
    res = client.get("/api/v1/ai/router/rules", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) > 0

    # 4. Test simulate route decision
    res = client.post("/api/v1/ai/router/simulate", json={
        "prompt": "Hello",
        "request_type": "chat",
        "strategy": "cheapest",
        "environment": "development"
    }, headers=headers)
    assert res.status_code == 200
    assert "selected_model" in res.json()
    assert "reason" in res.json()

    # 5. Test delete rule
    res = client.delete(f"/api/v1/ai/router/rules/{rule_id}", headers=headers)
    assert res.status_code == 204
