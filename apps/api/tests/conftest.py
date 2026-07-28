import datetime
import os

# Override key environment variables to ensure all tests run in mock mode
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID as PG_UUID
from api.database.session import get_db
from api.models import Base
from api.main import app

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(PG_UUID, "sqlite")
def compile_pg_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

# Use SQLite in-memory shared cache for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
)

@event.listens_for(engine, "connect")
def register_sqlite_now(dbapi_connection, connection_record):
    # Teach SQLite what now() is for compatibility with PostgreSQL migrations
    dbapi_connection.create_function("now", 0, lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    # Enable WAL mode for concurrent readers & writer
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """
    Setup clean database tables before executing tests, and drop them after.
    """
    import api.database.session
    import api.repositories.unit_of_work
    
    orig_db_session_local = api.database.session.SessionLocal
    orig_uow_session_local = api.repositories.unit_of_work.SessionLocal
    
    api.database.session.SessionLocal = TestingSessionLocal
    api.repositories.unit_of_work.SessionLocal = TestingSessionLocal
    
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass
        
    api.database.session.SessionLocal = orig_db_session_local
    api.repositories.unit_of_work.SessionLocal = orig_uow_session_local


@pytest.fixture(scope="function")
def db_session():
    """
    Function-scoped database session for test isolation.
    """
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function", autouse=True)
def override_db(db_session):
    """
    Override get_db FastAPI dependency to use test session.
    """
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


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
    def keys(self, pattern):
        import fnmatch
        # fnmatch needs pattern matching
        return [k for k in self.store.keys() if fnmatch.fnmatch(k, pattern)]
    def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                count += 1
        return count
    def ping(self):
        return True
    def info(self):
        return {"connected_clients": 1, "used_memory_human": "1MB"}


@pytest.fixture(scope="function", autouse=True)
def patch_redis(monkeypatch):
    from api.core.redis_manager import RedisConnectionManager
    mock_client = MockRedisClient()
    monkeypatch.setattr(RedisConnectionManager, "get_client", lambda self: mock_client)
    monkeypatch.setattr(RedisConnectionManager, "connect", lambda self: None)


def mock_chat(self, messages, model, temperature=0.7, **kwargs):
    provider_name = getattr(self, "provider_name", "mock")
    if hasattr(self, "__class__"):
        class_name = self.__class__.__name__.lower()
        if "groq" in class_name:
            provider_name = "groq"
        elif "openai" in class_name:
            provider_name = "openai"
        elif "claude" in class_name:
            provider_name = "anthropic"
        elif "gemini" in class_name:
            provider_name = "google"
        elif "openrouter" in class_name:
            provider_name = "openrouter"
            
    if "gemini" in model or provider_name == "google":
        content = f"Gemini Router ({model}) simulated response. Mocked AI Response Content"
    else:
        content = f"[Simulated response for {model}] Mocked AI Response Content"
    for m in messages:
        if m.get("role") == "system":
            if "System Context:" in m.get("content", "") or "Use the following" in m.get("content", ""):
                content += f"\n\nSystem Context:\n{m['content']}"
            else:
                content += f" {m['content']}"

    return {
        "content": content,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms": 100,
        "provider": provider_name,
        "model": model,
    }

def mock_stream(self, messages, model, temperature=0.7, **kwargs):
    yield {
        "content": "[Simulated chunk]",
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }

def mock_embeddings(self, text, model):
    return [0.1] * 1536

def mock_vision(self, prompt, image_url, model):
    provider_name = "mock"
    if hasattr(self, "__class__"):
        class_name = self.__class__.__name__.lower()
        if "gemini" in class_name:
            provider_name = "google"
            
    return {
        "content": f"[Simulated response for vision] Mocked vision response",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms": 100,
        "provider": provider_name,
        "model": model,
    }

def mock_json_output(self, messages, schema, model):
    return {
        "content": "{}",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms": 100,
        "provider": "mock",
        "model": model,
    }

def mock_health(self):
    return True


@pytest.fixture(scope="function", autouse=True)
def patch_ai_gateway_adapters(monkeypatch):
    from api.ai.providers.openai import OpenAIProvider
    from api.ai.providers.groq import GroqProvider
    from api.ai.providers.claude import ClaudeProvider
    from api.ai.providers.gemini import GeminiProvider
    from api.ai.providers.openrouter import OpenRouterProvider

    for provider_cls in [OpenAIProvider, GroqProvider, ClaudeProvider, GeminiProvider, OpenRouterProvider]:
        monkeypatch.setattr(provider_cls, "chat", mock_chat)
        monkeypatch.setattr(provider_cls, "stream", mock_stream)
        monkeypatch.setattr(provider_cls, "embeddings", mock_embeddings)
        monkeypatch.setattr(provider_cls, "vision", mock_vision)
        monkeypatch.setattr(provider_cls, "json_output", mock_json_output)
        monkeypatch.setattr(provider_cls, "health", mock_health)


@pytest.fixture(scope="session", autouse=True)
def configure_test_celery():
    try:
        from api.worker.celery_app import celery_app
        celery_app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
            result_backend="cache+memory://",
            broker_url="memory://",
        )
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def mock_minio_client():
    from minio.error import S3Error
    import io

    class MockResponse:
        status = 404
        headers = {}
        data = b""

    class MockMinioClient:
        def __init__(self, *args, **kwargs):
            self._storage = {}
            self._buckets = set()

        def bucket_exists(self, bucket_name):
            return bucket_name in self._buckets

        def make_bucket(self, bucket_name):
            self._buckets.add(bucket_name)

        def put_object(self, bucket_name, object_name, data, length, content_type=None):
            self._storage[(bucket_name, object_name)] = data.read()
            return None

        def get_object(self, bucket_name, object_name):
            content = self._storage.get((bucket_name, object_name))
            if content is None:
                raise S3Error(
                    code="NoSuchKey",
                    message="The specified key does not exist.",
                    resource=object_name,
                    request_id="mock-req",
                    host_id="mock-host",
                    response=MockResponse()
                )
            bio = io.BytesIO(content)
            bio.release_conn = lambda: None
            return bio

        def remove_object(self, bucket_name, object_name):
            self._storage.pop((bucket_name, object_name), None)
            return None

        def presigned_get_object(self, bucket_name, object_name, expires=None):
            return f"http://localhost:9000/{bucket_name}/{object_name}?token=mock-presigned-token"

    import minio
    minio.Minio = MockMinioClient
    try:
        import api.services.storage_service
        api.services.storage_service.Minio = MockMinioClient
    except ImportError:
        pass

    import httpx
    original_get = httpx.get

    def mock_get(url, *args, **kwargs):
        if "duckduckgo.com" in str(url):
            class MockResponse:
                status_code = 200
                text = """
                <div class="result__body">
                    <a class="result__title">Generative AI Tutorial</a>
                    <div class="result__snippet">Learn about Generative AI.</div>
                    <span class="result__url">https://example.com/genai</span>
                </div>
                <div class="result__body">
                    <a class="result__title">Generative AI Models</a>
                    <div class="result__snippet">Discover modern Generative AI models.</div>
                    <span class="result__url">https://example.com/models</span>
                </div>
                """
                def json(self):
                    return {}
            return MockResponse()
        return original_get(url, *args, **kwargs)

    httpx.get = mock_get


