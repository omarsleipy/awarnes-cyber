"""
Shared pytest fixtures.

Requires PostgreSQL (same schema family as production). Default URL targets port **35433**
(host `localhost` or `127.0.0.1`), matching a typical Docker mapping `35433:5432`.

  set TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:35433/cyberaware_test
  set CYBERAWARE_TESTING=1

The database is created automatically if missing (connects to the `postgres` maintenance DB first).
"""

from __future__ import annotations

import asyncio
import os
import sys

# Windows: default Proactor loop + asyncpg/SQLAlchemy can leave broken pools after each test loop.
# Set Selector policy before any asyncio.run() (see _ensure_postgres_database_exists below).
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass

# ── Environment BEFORE any application imports ───────────────────────────────
os.environ.setdefault("CYBERAWARE_TESTING", "1")
# Force DB URL into os.environ so pydantic-settings does not pick DATABASE_URL only from Backend/.env
# (would otherwise bypass setdefault and miss the Docker-mapped port 35433).
_default_test_db = (
    os.environ.get("TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql+asyncpg://postgres:postgres@127.0.0.1:35433/cyberaware_test"
)
os.environ["DATABASE_URL"] = _default_test_db
os.environ.setdefault("JWT_SECRET", "pytest-jwt-secret-change-in-ci-only-32chars")
os.environ.setdefault("SMTP_MOCK_MODE", "false")
os.environ.setdefault("APP_BASE_URL", "http://testserver")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:8080")


def _ensure_postgres_database_exists() -> None:
    """CREATE DATABASE if missing so CI/local runs do not fail on first-time setup."""
    raw = os.environ.get("DATABASE_URL") or ""
    if not raw.startswith("postgresql"):
        return
    try:
        import asyncpg
        from sqlalchemy.engine.url import make_url
    except ImportError:
        return

    try:
        url = make_url(raw)
    except Exception:
        return

    dbname = url.database
    if not dbname:
        return

    async def _run() -> None:
        kwargs = dict(
            user=url.username or "postgres",
            password=url.password or "",
            host=url.host or "localhost",
            port=url.port or 5432,
            database="postgres",
        )
        if os.getenv("CYBERAWARE_TESTING"):
            kwargs["ssl"] = False
        conn = await asyncpg.connect(**kwargs)
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                dbname,
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE "{dbname}"')
        finally:
            await conn.close()

    try:
        asyncio.run(_run())
    except Exception:
        pass


_ensure_postgres_database_exists()


def _clear_settings_cache() -> None:
    try:
        from config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


_clear_settings_cache()


def pytest_configure(config):
    """Ensure Windows keeps Selector policy after other plugins mutate the loop."""
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass


from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal, Base, engine
from core.security import hash_password
from main import app
from modules.organizations.models import Organization
from modules.users.models import User


def _import_all_models_for_schema() -> None:
    from modules.courses.models import Course, UserCourseProgress  # noqa: F401
    from modules.exams.models import (  # noqa: F401
        Certificate,
        Exam,
        ExamPassword,
        ExamQuestion,
        ExamSession,
    )
    from modules.monitoring.models import SuspiciousActivity  # noqa: F401
    from modules.phishing.models import PhishingCampaign, PhishingRecipient  # noqa: F401
    from modules.settings.models import Setting  # noqa: F401


_schema_initialized = False


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


async def _truncate_all() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE settings RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE TABLE organizations RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
async def _clean_tables() -> AsyncIterator[None]:
    """Ensure schema exists once, then truncate between tests (same asyncio loop as pytest-asyncio)."""
    global _schema_initialized
    if not _schema_initialized:
        _import_all_models_for_schema()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # create_all does not ALTER existing tables; match app startup compatibility.
        from main import _ensure_schema_compatibility

        await _ensure_schema_compatibility()
        _schema_initialized = True
    await _truncate_all()
    yield
    # pytest-asyncio uses a fresh event loop per test by default; recycle the pool so asyncpg is not tied to a closed loop.
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def two_orgs_with_users(db_session: AsyncSession):
    """Org Alpha / Org Beta with one admin + one trainee each."""
    org_a = Organization(name="Org Alpha Test", status="active", auth_mode="local")
    org_b = Organization(name="Org Beta Test", status="active", auth_mode="local")
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    pwd = hash_password("TestPass123!")
    users = [
        User(
            organization_id=org_a.id,
            email="admin.alpha@example.com",
            name="Admin Alpha",
            role="admin",
            department="IT",
            hashed_password=pwd,
        ),
        User(
            organization_id=org_a.id,
            email="trainee.alpha@example.com",
            name="Trainee Alpha",
            role="trainee",
            department="Finance",
            hashed_password=pwd,
        ),
        User(
            organization_id=org_b.id,
            email="admin.beta@example.com",
            name="Admin Beta",
            role="admin",
            department="IT",
            hashed_password=pwd,
        ),
        User(
            organization_id=org_b.id,
            email="trainee.beta@example.com",
            name="Trainee Beta",
            role="trainee",
            department="HR",
            hashed_password=pwd,
        ),
        User(
            organization_id=org_a.id,
            email="super.admin@example.com",
            name="Super Admin QA",
            role="super_admin",
            department="IT",
            hashed_password=pwd,
        ),
    ]
    db_session.add_all(users)
    await db_session.commit()
    admin_a, trainee_a, admin_b, trainee_b, super_u = users
    return {
        "org_a_id": org_a.id,
        "org_b_id": org_b.id,
        "admin_a_user_id": admin_a.id,
        "admin_b_user_id": admin_b.id,
        "trainee_a_user_id": trainee_a.id,
        "trainee_b_user_id": trainee_b.id,
        "super_admin_user_id": super_u.id,
        "admin_a_email": "admin.alpha@example.com",
        "admin_b_email": "admin.beta@example.com",
        "trainee_a_email": "trainee.alpha@example.com",
        "super_admin_email": "super.admin@example.com",
        "password": "TestPass123!",
    }


@pytest.fixture
def mock_aiosmtplib_send(monkeypatch):
    """Prevent real SMTP; capture calls."""
    mock = AsyncMock(return_value=None)
    import aiosmtplib

    monkeypatch.setattr(aiosmtplib, "send", mock)
    return mock


async def login_json(client: AsyncClient, email: str, password: str, organization_id: int | None = None) -> dict:
    body: dict = {"email": email, "password": password}
    if organization_id is not None:
        body["organizationId"] = str(organization_id)
    r = await client.post("/api/auth/login", json=body)
    return {"status": r.status_code, "json": r.json() if r.headers.get("content-type", "").startswith("application/json") else {}}


@pytest.fixture
def login_helper(client: AsyncClient):
    async def _login(email: str, password: str, organization_id: int | None = None) -> str:
        res = await login_json(client, email, password, organization_id)
        assert res["status"] == 200, res
        data = res["json"]
        assert data.get("success") is True
        return data["token"]

    return _login
