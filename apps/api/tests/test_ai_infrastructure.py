import pytest
import fnmatch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from api.models.user import User
from api.models.membership import UserOrganization
from api.core.redis_manager import RedisConnectionManager
from api.services.cache_service import CacheService
from api.services.queue_service import QueueService

client = TestClient(app)

class MockRedisClient:
    def __init__(self):
        self.store = {}
        self.queues = {}

    def ping(self):
        return True

    def info(self):
        return {"connected_clients": 1, "used_memory_human": "1.2M"}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value
        return True

    def setex(self, key, ttl, value):
        self.store[key] = value
        return True

    def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                count += 1
            if k in self.queues:
                del self.queues[k]
                count += 1
        return count

    def keys(self, pattern):
        all_keys = list(self.store.keys()) + list(self.queues.keys())
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def rpush(self, key, value):
        if key not in self.queues:
            self.queues[key] = []
        self.queues[key].append(value)
        return len(self.queues[key])

    def lpop(self, key):
        if key in self.queues and self.queues[key]:
            return self.queues[key].pop(0)
        return None

    def llen(self, key):
        if key in self.queues:
            return len(self.queues[key])
        return 0

    def zadd(self, key, mapping):
        if key not in self.queues:
            self.queues[key] = []
        for val, score in mapping.items():
            self.queues[key] = [item for item in self.queues[key] if item[0] != val]
            self.queues[key].append((val, score))
        self.queues[key].sort(key=lambda x: x[1])
        return len(self.queues[key])

    def zpopmin(self, key, count=1):
        if key in self.queues and self.queues[key]:
            popped = []
            for _ in range(min(count, len(self.queues[key]))):
                val, score = self.queues[key].pop(0)
                popped.append((val, score))
            return popped
        return []

    def zcard(self, key):
        if key in self.queues:
            return len(self.queues[key])
        return 0


from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def patch_redis(monkeypatch):
    mock_client = MockRedisClient()
    monkeypatch.setattr(RedisConnectionManager, "get_client", lambda self: mock_client)
    monkeypatch.setattr(RedisConnectionManager, "connect", lambda self: None)
    
    mock_async_res = MagicMock()
    mock_async_res.id = "mock-task-id-123"
    from api.worker.celery_app import celery_app
    monkeypatch.setattr(celery_app, "send_task", lambda *args, **kwargs: mock_async_res)


def test_redis_connection_manager():
    manager = RedisConnectionManager()
    client_inst = manager.get_client()
    assert client_inst is not None
    
    metrics = manager.get_metrics()
    assert metrics["status"] == "connected"
    assert "latency_ms" in metrics
    assert "connected_clients" in metrics

def test_cache_service():
    cache = CacheService()
    cache.hits_count = 0
    cache.misses_count = 0
    
    assert cache.set(namespace="prompt", key="t1", value={"test": "ok"}, ttl=30) is True
    val = cache.get(namespace="prompt", key="t1")
    assert val == {"test": "ok"}
    assert cache.hits_count == 1
    assert cache.misses_count == 0

    val_miss = cache.get(namespace="prompt", key="non_existent")
    assert val_miss is None
    assert cache.misses_count == 1

    assert cache.set(namespace="response", key="c1", value="a" * 100, ttl=30, compress=True) is True
    val_c = cache.get(namespace="response", key="c1")
    assert val_c == "a" * 100

    assert cache.delete(namespace="prompt", key="t1") is True
    assert cache.get(namespace="prompt", key="t1") is None

    cache.set(namespace="prompt", key="t2", value="v2")
    cache.set(namespace="prompt", key="t3", value="v3")
    cleared = cache.clear_namespace(namespace="prompt")
    assert cleared >= 2
    assert cache.get(namespace="prompt", key="t2") is None

def test_queue_service():
    q = QueueService()
    q.clear("ai_requests")
    
    assert q.get_size("ai_requests") == 0
    
    assert q.enqueue("ai_requests", {"id": "req-1"}) is True
    assert q.enqueue("ai_requests", {"id": "req-2"}) is True
    
    assert q.get_size("ai_requests") == 2
    
    item1 = q.dequeue("ai_requests")
    assert item1 == {"id": "req-1"}
    item2 = q.dequeue("ai_requests")
    assert item2 == {"id": "req-2"}
    assert q.dequeue("ai_requests") is None

    assert q.enqueue("ai_requests", {"id": "low"}, priority=1) is True
    assert q.enqueue("ai_requests", {"id": "high"}, priority=10) is True
    
    assert q.dequeue("ai_requests") == {"id": "high"}
    assert q.dequeue("ai_requests") == {"id": "low"}

def test_infrastructure_api_routes(db_session: Session):
    email = "infratest@example.com"
    password = "secretpassword123"
    
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Infra Admin",
        "password": password,
        "org_name": "Infra Test Org"
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

    res = client.get("/api/v1/ai/infrastructure/health", headers=headers)
    assert res.status_code == 200
    assert "redis" in res.json()
    assert "database" in res.json()

    res = client.get("/api/v1/ai/infrastructure/redis", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "connected"

    res = client.get("/api/v1/ai/infrastructure/cache", headers=headers)
    assert res.status_code == 200
    assert "hits" in res.json()

    res = client.post("/api/v1/ai/infrastructure/cache/clear", json={"namespace": "playground"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    res = client.get("/api/v1/ai/infrastructure/queues", headers=headers)
    assert res.status_code == 200
    assert "ai_requests" in res.json()

    res = client.get("/api/v1/ai/infrastructure/workers", headers=headers)
    assert res.status_code == 200
    assert "jobs" in res.json()

    res = client.get("/api/v1/ai/infrastructure/jobs", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    res = client.post("/api/v1/ai/infrastructure/jobs/run", json={"task_name": "worker.tasks.health_worker_task"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "task_id" in res.json()
