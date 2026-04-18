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

_engine_kw = dict(
    echo=False,
    pool_pre_ping=True,
    pool_timeout=60,
    pool_size=20,
    max_overflow=10,
)
if os.getenv("CYBERAWARE_TESTING"):
    # Fresh checkout per use avoids asyncpg connections tied to a closed pytest-asyncio loop on Windows.
    _engine_kw["poolclass"] = NullPool
    # NullPool does not accept queue-pool sizing arguments.
    for _k in ("pool_timeout", "pool_size", "max_overflow"):
        _engine_kw.pop(_k, None)

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
