import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from api.core.config import settings

# Replace postgresql:// with postgresql+asyncpg:// for async connection
# (P2-9): honor an explicit ASYNC_DATABASE_URL when configured.
async_db_url = settings.ASYNC_DATABASE_URL or settings.DATABASE_URL
if async_db_url.startswith("postgresql://"):
    async_db_url = async_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(
    async_db_url,
    pool_pre_ping=True,
    pool_size=50,
    max_overflow=100,
)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an AsyncSession.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
