"""Database queries for users."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.models import User


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession, skip: int = 0, limit: int = 500) -> list[User]:
    result = await session.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create(session: AsyncSession, email: str, hashed_password: str, name: str, role: str = "trainee", department: str = "") -> User:
    user = User(
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
