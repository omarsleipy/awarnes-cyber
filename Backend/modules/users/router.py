"""User management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id, require_admin
from modules.users.schemas import BulkUploadRequest, UserCreate, UserResponse
from modules.users.service import add_user, bulk_upload_users, list_users

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def get_users(
    _: int = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    return await list_users(session)


@router.post("", response_model=UserResponse)
async def post_user(
    body: UserCreate,
    _: int = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    try:
        return await add_user(session, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/bulk-upload")
async def post_bulk_upload(
    body: BulkUploadRequest,
    _: int = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    return await bulk_upload_users(session, body.csvData)
