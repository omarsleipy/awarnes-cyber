"""Alembic migration environment (sync driver; app runtime uses asyncpg)."""
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

from alembic import context

from config import get_settings
from core.database import Base

# Import all models so Base.metadata is complete for autogenerate
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

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_database_url() -> str:
    """Alembic runs migrations with a synchronous driver (psycopg2)."""
    raw = get_settings().DB_URL
    u = make_url(raw)
    if u.drivername == "postgresql+asyncpg":
        u = u.set(drivername="postgresql+psycopg2")
    return u.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    url = _sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        _sync_database_url(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
