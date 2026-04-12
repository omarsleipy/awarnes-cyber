"""Course queries and progress."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.courses.models import Course, UserCourseProgress


async def list_courses(session: AsyncSession) -> list[Course]:
    r = await session.execute(select(Course).order_by(Course.id))
    return list(r.scalars().all())


async def get_progress(session: AsyncSession, user_id: int, course_id: str) -> UserCourseProgress | None:
    r = await session.execute(
        select(UserCourseProgress).where(UserCourseProgress.user_id == user_id, UserCourseProgress.course_id == course_id)
    )
    return r.scalar_one_or_none()


async def upsert_progress(session: AsyncSession, user_id: int, course_id: str, viewed_slides: int) -> UserCourseProgress:
    row = await get_progress(session, user_id, course_id)
    if row:
        row.viewed_slides = viewed_slides
        await session.flush()
        await session.refresh(row)
        return row
    row = UserCourseProgress(user_id=user_id, course_id=course_id, viewed_slides=viewed_slides)
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


async def ensure_seed_courses(session: AsyncSession) -> None:
    """Insert default courses if table is empty."""
    r = await session.execute(select(Course).limit(1))
    if r.scalar_one_or_none():
        return
    seed = [
        Course(
            id="c1",
            title="Phishing Awareness Fundamentals",
            modules=8,
            duration="45 min",
            total_slides=24,
            exam_id="e1",
            category="Phishing",
        ),
        Course(
            id="c2",
            title="Email Security Best Practices",
            modules=6,
            duration="30 min",
            total_slides=18,
            exam_id="e2",
            category="Email Security",
        ),
        Course(
            id="c3",
            title="Data Privacy & GDPR Compliance",
            modules=12,
            duration="60 min",
            total_slides=36,
            exam_id="e3",
            category="Data Privacy",
        ),
        Course(
            id="c4",
            title="Password Hygiene & MFA",
            modules=4,
            duration="20 min",
            total_slides=12,
            exam_id=None,
            category="Access Control",
        ),
    ]
    for c in seed:
        session.add(c)
    await session.flush()
