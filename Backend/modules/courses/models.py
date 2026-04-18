"""Courses and per-user progress."""
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True, default=1)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    modules: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[str] = mapped_column(String(64), default="")
    total_slides: Mapped[int] = mapped_column(Integer, default=0)
    exam_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str] = mapped_column(String(128), default="")
    # LMS: text | video | hybrid (mixed unit types below)
    content_type: Mapped[str] = mapped_column(String(32), default="text")
    # Ordered units: {"type":"text"|"video"|"image", ...}
    content_units: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Mid-content quizzes: [{"id","afterUnitIndex","enabled","questions":[{...}]}]
    mid_quizzes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    certificate_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    certificate_template_key: Mapped[str] = mapped_column(String(64), default="default")


class UserCourseProgress(Base):
    __tablename__ = "user_course_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True, default=1)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    viewed_slides: Mapped[int] = mapped_column(Integer, default=0)
    # Per mid-quiz id: { "mq1": { "q1": 0, "q2": 1 } }
    quiz_responses: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_user_course"),)
