"""Phishing campaign queries."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.phishing.models import PhishingCampaign


async def list_all(session: AsyncSession) -> list[PhishingCampaign]:
    r = await session.execute(select(PhishingCampaign).order_by(PhishingCampaign.created_at.desc()))
    return list(r.scalars().all())


async def create(
    session: AsyncSession,
    *,
    name: str,
    template: str = "",
    target_dept: str = "All",
) -> PhishingCampaign:
    c = PhishingCampaign(name=name, template=template, target_dept=target_dept, status="draft")
    session.add(c)
    await session.flush()
    await session.refresh(c)
    return c
