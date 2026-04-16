"""Initial schema from SQLAlchemy models.

Revision ID: 001_initial
Revises:
Create Date: 2026-04-15

Uses ``Base.metadata.create_all`` so the first revision matches all registered models
without requiring a live DB at revision-authoring time.
"""

from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from core.database import Base
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

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from core.database import Base
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

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
