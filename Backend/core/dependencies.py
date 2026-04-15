"""FastAPI dependencies: JWT auth."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import decode_access_token
from modules.organizations.repository import get_by_id as org_get_by_id
from modules.users.repository import get_by_id as user_get_by_id

security = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> object:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        uid = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await user_get_by_id(session, uid)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    organization = await org_get_by_id(session, user.organization_id)
    if organization and organization.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization is suspended")
    return user


async def get_current_user_id(
    user: Annotated[object, Depends(get_current_user)],
) -> int:
    return int(user.id)


async def get_current_organization_id(
    user: Annotated[object, Depends(get_current_user)],
) -> int:
    return int(user.organization_id)


async def require_admin(
    user: Annotated[object, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> int:
    if not user or user.role not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return int(user.id)


async def require_super_admin(
    user: Annotated[object, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> int:
    if not user or user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is suspended")
    return int(user.id)
