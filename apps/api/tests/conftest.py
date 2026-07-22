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
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass


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
