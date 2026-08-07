import datetime
import os

# Override key environment variables to ensure all tests run in mock mode
os.environ["ENVIRONMENT"] = "test"

# Support parallel testing with pytest-xdist by using worker-specific databases
worker_id = os.environ.get("PYTEST_XDIST_WORKER")
if worker_id:
    db_name = f"eaimos_test_{worker_id}"
else:
    db_name = "eaimos_test"

os.environ["DATABASE_URL"] = f"postgresql://postgres:postgres@localhost:5432/{db_name}"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["SECRET_KEY"] = "SUPER_SECRET_JWT_KEY_MIN_32_CHARS_LONG_PLEASE_REPLACE_IN_PRODUCTION"
os.environ["RESEND_API_KEY"] = ""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database.session import get_db
from api.models import Base
from api.main import app
from api.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def pytest_configure(config):
    # Only run on the master process (not on xdist workers)
    if not hasattr(config, "workerinput"):
        import os
        from sqlalchemy import create_engine as pg_create_engine, text
        from alembic.config import Config
        from alembic import command
        
        num_workers = config.option.numprocesses
        if num_workers == "auto":
            import multiprocessing
            num_workers = multiprocessing.cpu_count()
        elif num_workers is not None:
            try:
                num_workers = int(num_workers)
            except ValueError:
                num_workers = None
                
        if num_workers and num_workers > 1:
            print(f"\n[Master] Pre-initializing {num_workers} parallel test databases sequentially...")
            system_engine = pg_create_engine("postgresql://postgres:postgres@localhost:5432/postgres", isolation_level="AUTOCOMMIT")
            
            tests_dir = os.path.dirname(os.path.abspath(__file__))
            api_dir = os.path.dirname(tests_dir)
            alembic_ini_path = os.path.join(api_dir, "alembic.ini")
            alembic_cfg = Config(alembic_ini_path)
            alembic_cfg.set_main_option("script_location", os.path.join(api_dir, "alembic"))
            
            for i in range(num_workers):
                worker_db = f"eaimos_test_gw{i}"
                print(f"[Master] Creating and migrating {worker_db}...")
                
                with system_engine.connect() as conn:
                    db_exists = conn.execute(
                        text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                        {"dbname": worker_db}
                    ).scalar()
                    if not db_exists:
                        conn.execute(text(f"CREATE DATABASE {worker_db};"))
                
                worker_url = f"postgresql://postgres:postgres@localhost:5432/{worker_db}"
                worker_engine = pg_create_engine(worker_url)
                
                with worker_engine.begin() as conn:
                    conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
                    conn.execute(text("CREATE SCHEMA public;"))
                    conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
                
                worker_engine.dispose()
                
                # Run migrations in a subprocess with DATABASE_URL set to worker_url
                import subprocess
                env = os.environ.copy()
                env["DATABASE_URL"] = worker_url
                env["ENVIRONMENT"] = "test"
                res = subprocess.run(
                    ["poetry", "run", "alembic", "-c", alembic_ini_path, "upgrade", "head"],
                    env=env,
                    capture_output=True,
                    text=True
                )
                if res.returncode != 0:
                    print(f"[Master] Migration failed for {worker_db}: {res.stderr}")
                    raise RuntimeError(f"Migration failed for {worker_db}: {res.stderr}")
                
            system_engine.dispose()
            print("[Master] All parallel test databases initialized successfully.")


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """
    Setup clean database tables before executing tests, and drop them after.
    Runs Alembic migrations to construct the database schema if running sequentially.
    For parallel workers, uses the pre-initialized database directly.
    """
    import api.database.session
    import api.repositories.unit_of_work
    
    orig_db_session_local = api.database.session.SessionLocal
    orig_uow_session_local = api.repositories.unit_of_work.SessionLocal
    
    api.database.session.SessionLocal = TestingSessionLocal
    api.repositories.unit_of_work.SessionLocal = TestingSessionLocal
    
    # If this is a parallel worker, the master has already initialized and migrated the DB
    if os.environ.get("PYTEST_XDIST_WORKER"):
        yield
        engine.dispose()
        api.database.session.SessionLocal = orig_db_session_local
        api.repositories.unit_of_work.SessionLocal = orig_uow_session_local
        return

    # Sequential run fallback database creation and migration
    from sqlalchemy import create_engine as pg_create_engine, text
    system_engine = pg_create_engine("postgresql://postgres:postgres@localhost:5432/postgres", isolation_level="AUTOCOMMIT")
    with system_engine.connect() as conn:
        db_exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": db_name}
        ).scalar()
        if not db_exists:
            conn.execute(text(f"CREATE DATABASE {db_name};"))
    system_engine.dispose()
    
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.dirname(tests_dir)
    alembic_ini_path = os.path.join(api_dir, "alembic.ini")
    
    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(api_dir, "alembic"))
    
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
        
    command.upgrade(alembic_cfg, "head")
    
    yield
    
    engine.dispose()
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
    except Exception:
        pass
        
    api.database.session.SessionLocal = orig_db_session_local
    api.repositories.unit_of_work.SessionLocal = orig_uow_session_local


@pytest.fixture(scope="function")
def db_session():
    """
    Function-scoped database session for test isolation.
    Uses connection-level savepoint/transaction rollback for 100% isolation on PostgreSQL.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    # Configure sessionmaker to bind to the active connection for shared transactions
    TestingSessionLocal.configure(bind=connection)
    
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
    
    # Restore sessionmaker to use the engine
    TestingSessionLocal.configure(bind=engine)


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


