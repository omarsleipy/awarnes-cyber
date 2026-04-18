"""Courses routes."""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_organization_id, get_current_user_id
from modules.courses import service as courses_service

router = APIRouter()


class ProgressBody(BaseModel):
    viewedSlides: int
    quizResponses: dict | None = None


@router.get("")
async def get_courses(
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    return await courses_service.list_for_user(session, organization_id, user_id)


@router.get("/{course_id}")
async def get_course_detail(
    course_id: str,
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    detail = await courses_service.get_course_detail(session, organization_id, user_id, course_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Course not found")
    return detail


@router.patch("/{course_id}/progress")
async def patch_progress(
    course_id: str,
    body: ProgressBody,
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    await courses_service.update_progress(
        session,
        organization_id,
        user_id,
        course_id,
        body.viewedSlides,
        quiz_responses_patch=body.quizResponses,
    )
    return {"success": True}
