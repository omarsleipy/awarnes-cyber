"""Auth business logic: login, token creation."""
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_password, create_access_token
from modules.users.repository import get_by_email, update_last_login


async def login(session: AsyncSession, email: str, password: str) -> dict:
    """
    Returns either:
    - {"success": True, "user": {...}, "token": "..."}
    - {"success": False, "error": "..."}
    """
    user = await get_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        return {"success": False, "error": "Invalid credentials"}
    if user.status != "active":
        return {"success": False, "error": "Account is suspended"}
    await update_last_login(session, user.id)
    token = create_access_token(user.id, extra={"email": user.email, "role": user.role})
    return {
        "success": True,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "status": user.status,
            "completedCourses": user.completed_courses,
            "lastLogin": user.last_login.strftime("%Y-%m-%d") if user.last_login else "Never",
        },
        "token": token,
    }
