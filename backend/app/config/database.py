"""
HomeCare+ — PostgreSQL configuration (SQLAlchemy 2.0 async + asyncpg).

    from app.config.database import get_db
    async def route(db: AsyncSession = Depends(get_db)): ...

Schema changes are managed by Alembic (see backend/alembic/); the app never
calls create_all() in normal operation.
"""
import logging
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,              # transparently replace dead connections
)

# expire_on_commit=False lets routes read attributes of an object after commit
# without triggering a lazy refresh (which is not allowed in async code).
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, rolled back on error."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def ping_database() -> bool:
    """Check PostgreSQL connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False


async def close_database() -> None:
    """Dispose the connection pool (call on app shutdown)."""
    await engine.dispose()
