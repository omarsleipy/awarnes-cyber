"""User business logic."""
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from modules.users.repository import get_by_email, create, get_all, get_by_id
from modules.users.schemas import UserCreate, UserResponse, BulkUploadResult


def _user_to_response(user) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        department=user.department,
        status=user.status,
        completedCourses=user.completed_courses,
        lastLogin=user.last_login.strftime("%Y-%m-%d") if user.last_login else "Never",
    )


async def get_user_by_email(session: AsyncSession, email: str):
    return await get_by_email(session, email)


async def get_user_by_id(session: AsyncSession, user_id: int):
    return await get_by_id(session, user_id)


async def list_users(session: AsyncSession, skip: int = 0, limit: int = 500) -> list[UserResponse]:
    users = await get_all(session, skip=skip, limit=limit)
    return [_user_to_response(u) for u in users]


async def add_user(session: AsyncSession, payload: UserCreate) -> UserResponse:
    existing = await get_by_email(session, payload.email)
    if existing:
        raise ValueError("User with this email already exists")
    user = await create(
        session,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        department=payload.department,
    )
    return _user_to_response(user)


async def bulk_upload_users(session: AsyncSession, csv_content: str) -> BulkUploadResult:
    """Parse CSV (name, email, department, role) and create users. Returns counts."""
    reader = csv.DictReader(io.StringIO(csv_content))
    imported = 0
    skipped = 0
    errors = 0
    required = {"name", "email", "department", "role"}
    for row in reader:
        row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
        # Normalize keys: name, email, department, role
        if not set(row.keys()) & required:
            errors += 1
            continue
        name = row.get("name") or row.get("full name") or ""
        email = row.get("email") or ""
        department = row.get("department") or ""
        role = (row.get("role") or "trainee").lower()
        if role not in ("admin", "trainee"):
            role = "trainee"
        if not name or not email:
            errors += 1
            continue
        existing = await get_by_email(session, email)
        if existing:
            skipped += 1
            continue
        try:
            await create(session, email=email, hashed_password=hash_password("ChangeMe123!"), name=name, role=role, department=department)
            imported += 1
        except Exception:
            errors += 1
    return BulkUploadResult(imported=imported, skipped=skipped, errors=errors)
