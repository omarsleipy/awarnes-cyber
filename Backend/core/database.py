"""Async SQLAlchemy engine and session management."""
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import get_settings

settings = get_settings()

# Async engine (use asyncpg for PostgreSQL async)
_connect_args = {}
if os.getenv("CYBERAWARE_TESTING") and "+asyncpg" in settings.DB_URL:
    # asyncpg defaults to TLS "prefer"; local Docker Postgres is usually non-TLS and on Windows
    # the SSL negotiation path can stall until timeout. Tests target plain Postgres on 35433.
    _connect_args["ssl"] = False
    _connect_args["timeout"] = 15

_engine_kw = dict(echo=False, pool_pre_ping=True)
if os.getenv("CYBERAWARE_TESTING"):
    # Fresh connection per checkout avoids stale asyncpg pools across pytest-asyncio loops on Windows.
    _engine_kw["poolclass"] = NullPool
else:
    _engine_kw["pool_size"] = 5
    _engine_kw["max_overflow"] = 10

engine = create_async_engine(
    settings.DB_URL,
    connect_args=_connect_args,
    **_engine_kw,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
