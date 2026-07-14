import datetime
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from api.database.session import get_db
from api.models import Base
from api.main import app

# Use SQLite local file for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def register_sqlite_now(dbapi_connection, connection_record):
    # Teach SQLite what now() is for compatibility with PostgreSQL migrations
    dbapi_connection.create_function("now", 0, lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """
    Setup clean database tables before executing tests, and drop them after.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Transaction-based database session rollback for test isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


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
