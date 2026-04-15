"""Database queries for users."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.models import User


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_email(session: AsyncSession, email: str, organization_id: int | None = None) -> User | None:
    stmt = select(User).where(User.email == email)
    if organization_id is not None:
        stmt = stmt.where(User.organization_id == organization_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_by_email(session: AsyncSession, email: str) -> list[User]:
    result = await session.execute(select(User).where(User.email == email))
    return list(result.scalars().all())


async def get_all(session: AsyncSession, organization_id: int, skip: int = 0, limit: int = 500) -> list[User]:
    result = await session.execute(
        select(User).where(User.organization_id == organization_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_department(
    session: AsyncSession,
    organization_id: int,
    department: str,
    limit: int = 2000,
) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.organization_id == organization_id, User.department == department)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create(
    session: AsyncSession,
    email: str,
    hashed_password: str,
    name: str,
    role: str = "trainee",
    department: str = "",
    organization_id: int = 1,
) -> User:
    user = User(
        organization_id=organization_id,
        email=email,
        hashed_password=hashed_password,
        name=name,
        role=role,
        department=department,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def update_last_login(session: AsyncSession, user_id: int) -> None:
    user = await get_by_id(session, user_id)
    if user:
        user.last_login = datetime.utcnow()
        await session.flush()
