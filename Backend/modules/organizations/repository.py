"""Organization queries."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.organizations.models import Organization


async def get_by_id(session: AsyncSession, organization_id: int) -> Organization | None:
    r = await session.execute(select(Organization).where(Organization.id == organization_id))
    return r.scalar_one_or_none()


async def get_by_name(session: AsyncSession, name: str) -> Organization | None:
    r = await session.execute(select(Organization).where(Organization.name == name))
    return r.scalar_one_or_none()


async def list_all(session: AsyncSession) -> list[Organization]:
    r = await session.execute(select(Organization).order_by(Organization.name.asc()))
    return list(r.scalars().all())


async def create(session: AsyncSession, name: str) -> Organization:
    org = Organization(name=name, status="active", auth_mode="local")
    session.add(org)
    await session.flush()
    await session.refresh(org)
    return org

