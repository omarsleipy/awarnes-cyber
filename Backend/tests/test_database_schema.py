"""ORM coverage and parity with public schema (Alembic / create_all)."""

from sqlalchemy import text

import pytest


def _import_all_models() -> None:
    """Register every table on Base.metadata (mirrors alembic env imports)."""
    from modules.courses.models import Course, UserCourseProgress  # noqa: F401
    from modules.exams.models import (  # noqa: F401
        Certificate,
        Exam,
        ExamPassword,
        ExamQuestion,
        ExamSession,
    )
    from modules.monitoring.models import SuspiciousActivity  # noqa: F401
    from modules.organizations.models import Organization  # noqa: F401
    from modules.phishing.models import PhishingCampaign, PhishingRecipient  # noqa: F401
    from modules.settings.models import Setting  # noqa: F401
    from modules.users.models import User  # noqa: F401


@pytest.mark.asyncio
async def test_sqlalchemy_registry_has_thirteen_tables():
    from core.database import Base

    _import_all_models()
    assert len(Base.metadata.tables) == 13


@pytest.mark.asyncio
async def test_public_schema_contains_all_mapped_tables(db_session):
    _import_all_models()
    from core.database import Base

    r = await db_session.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """
        )
    )
    db_names = {row[0] for row in r.fetchall()}
    for t in Base.metadata.tables.keys():
        assert t in db_names, f"Table {t} missing from database (run migrations / create_all)."
