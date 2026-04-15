"""Auth routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from modules.auth.schemas import LoginRequest
from modules.auth.service import login as do_login

router = APIRouter()


@router.post("/login")
async def auth_login(body: LoginRequest, session: AsyncSession = Depends(get_db)):
    result = await do_login(session, body.email, body.password, organization_id=body.organizationId)
    return result
