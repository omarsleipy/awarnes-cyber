"""Courses API: static course rows, LMS content, progress, optional course certificates."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from modules.courses import repository as repo
from modules.courses.models import Course
from modules.exams import repository as exam_repo


def effective_content_unit_count(course: Course) -> int:
    units = course.content_units
    if isinstance(units, list) and len(units) > 0:
        return len(units)
    return max(1, course.total_slides or 1)


def _sanitize_mid_quizzes(quizzes: list | None) -> list:
    """Remove correct answers for learner-facing payloads."""
    if not quizzes:
        return []
    out: list[dict[str, Any]] = []
    for q in quizzes:
        if not isinstance(q, dict):
            continue
        if q.get("enabled") is False:
            continue
        item = {k: v for k, v in q.items() if k != "questions"}
        qs = q.get("questions") or []
        clean_qs = []
        for qq in qs:
            if not isinstance(qq, dict):
                continue
            clean_qs.append({k2: v2 for k2, v2 in qq.items() if k2 != "correctIndex"})
        item["questions"] = clean_qs
        out.append(item)
    return out


def _course_to_public_dict(
    *,
    course: Course,
    viewed: int,
    quiz_snapshot: dict | None,
) -> dict[str, Any]:
    total_units = effective_content_unit_count(course)
    progress = min(100, round((viewed / total_units) * 100)) if total_units else 0
    units = course.content_units if isinstance(course.content_units, list) else []
    return {
        "id": course.id,
        "title": course.title,
        "modules": course.modules,
        "duration": course.duration,
        "progress": progress,
        "totalSlides": total_units,
        "viewedSlides": viewed,
        "examId": course.exam_id,
        "category": course.category,
        "contentType": course.content_type or "text",
        "contentUnits": units,
        "midQuizzes": _sanitize_mid_quizzes(course.mid_quizzes if isinstance(course.mid_quizzes, list) else None),
        "quizResponses": quiz_snapshot or {},
        "certificateEnabled": bool(course.certificate_enabled),
        "certificateTemplateKey": course.certificate_template_key or "default",
    }


async def list_for_user(session: AsyncSession, organization_id: int, user_id: int) -> list[dict]:
    await repo.ensure_seed_courses(session, organization_id=organization_id)
    courses = await repo.list_courses(session, organization_id=organization_id)
    out: list[dict] = []
    for c in courses:
        p = await repo.get_progress(session, organization_id, user_id, c.id)
        viewed = p.viewed_slides if p else 0
        qr = (p.quiz_responses if p else None) or {}
        out.append(_course_to_public_dict(course=c, viewed=viewed, quiz_snapshot=qr))
    return out


async def maybe_issue_course_certificate(
    session: AsyncSession,
    organization_id: int,
    user_id: int,
    course: Course,
) -> None:
    if not course.certificate_enabled:
        return
    total = effective_content_unit_count(course)
    p = await repo.get_progress(session, organization_id, user_id, course.id)
    if not p or p.viewed_slides < total:
        return
    if await exam_repo.course_certificate_exists(session, user_id, course.id):
        return
    tmpl = course.certificate_template_key or "default"
    await exam_repo.certificate_create_for_course(
        session,
        user_id=user_id,
        course_id=course.id,
        course_title=course.title,
        score=100,
        template_key=tmpl,
    )


async def update_progress(
    session: AsyncSession,
    organization_id: int,
    user_id: int,
    course_id: str,
    viewed_slides: int,
    *,
    quiz_responses_patch: dict | None = None,
) -> None:
    course = await repo.get_course(session, organization_id, course_id)
    if not course:
        return
    await repo.upsert_progress(
        session,
        organization_id,
        user_id,
        course_id,
        viewed_slides,
        quiz_responses_patch=quiz_responses_patch,
    )
    await maybe_issue_course_certificate(session, organization_id, user_id, course)


async def get_course_detail(session: AsyncSession, organization_id: int, user_id: int, course_id: str) -> dict | None:
    await repo.ensure_seed_courses(session, organization_id=organization_id)
    course = await repo.get_course(session, organization_id, course_id)
    if not course:
        return None
    p = await repo.get_progress(session, organization_id, user_id, course_id)
    viewed = p.viewed_slides if p else 0
    qr = (p.quiz_responses if p else None) or {}
    return _course_to_public_dict(course=course, viewed=viewed, quiz_snapshot=qr)
