"""Courses routes."""
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id
from modules.courses import service as courses_service

router = APIRouter()


class ProgressBody(BaseModel):
    viewedSlides: int


@router.get("")
async def get_courses(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    return await courses_service.list_for_user(session, user_id)


@router.patch("/{course_id}/progress")
async def patch_progress(
    course_id: str,
    body: ProgressBody,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    await courses_service.update_progress(session, user_id, course_id, body.viewedSlides)
    return {"success": True}
