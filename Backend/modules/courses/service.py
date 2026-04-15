"""Courses API: merge static course rows with user progress."""
from sqlalchemy.ext.asyncio import AsyncSession

from modules.courses import repository as repo


async def list_for_user(session: AsyncSession, organization_id: int, user_id: int) -> list[dict]:
    await repo.ensure_seed_courses(session, organization_id=organization_id)
    courses = await repo.list_courses(session, organization_id=organization_id)
    out: list[dict] = []
    for c in courses:
        p = await repo.get_progress(session, organization_id, user_id, c.id)
        viewed = p.viewed_slides if p else 0
        total = c.total_slides or 1
        progress = min(100, round((viewed / total) * 100)) if total else 0
        out.append(
            {
                "id": c.id,
                "title": c.title,
                "modules": c.modules,
                "duration": c.duration,
                "progress": progress,
                "totalSlides": c.total_slides,
                "viewedSlides": viewed,
                "examId": c.exam_id,
                "category": c.category,
            }
        )
    return out


async def update_progress(
    session: AsyncSession,
    organization_id: int,
    user_id: int,
    course_id: str,
    viewed_slides: int,
) -> None:
    await repo.upsert_progress(session, organization_id, user_id, course_id, viewed_slides)
