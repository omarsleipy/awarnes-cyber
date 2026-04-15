"""Phishing campaign and tracking queries."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.phishing.models import PhishingCampaign, PhishingRecipient


async def list_all(session: AsyncSession, organization_id: int) -> list[PhishingCampaign]:
    r = await session.execute(
        select(PhishingCampaign)
        .where(PhishingCampaign.organization_id == organization_id)
        .order_by(PhishingCampaign.created_at.desc())
    )
    return list(r.scalars().all())


async def create(
    session: AsyncSession,
    *,
    organization_id: int,
    name: str,
    template: str = "",
    target_dept: str = "All",
) -> PhishingCampaign:
    c = PhishingCampaign(
        organization_id=organization_id,
        name=name,
        template=template,
        target_dept=target_dept,
        status="draft",
    )
    session.add(c)
    await session.flush()
    await session.refresh(c)
    return c


async def get_by_id(session: AsyncSession, campaign_id: int, organization_id: int | None = None) -> PhishingCampaign | None:
    stmt = select(PhishingCampaign).where(PhishingCampaign.id == campaign_id)
    if organization_id is not None:
        stmt = stmt.where(PhishingCampaign.organization_id == organization_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_status(session: AsyncSession, campaign_id: int, status: str, organization_id: int | None = None) -> None:
    campaign = await get_by_id(session, campaign_id, organization_id=organization_id)
    if campaign:
        campaign.status = status
        await session.flush()


async def recipient_create(
    session: AsyncSession,
    *,
    organization_id: int,
    campaign_id: int,
    user_id: int,
    email: str,
    destination_url: str,
    tracking_token: str,
) -> PhishingRecipient:
    rec = PhishingRecipient(
        organization_id=organization_id,
        campaign_id=campaign_id,
        user_id=user_id,
        email=email,
        destination_url=destination_url,
        tracking_token=tracking_token,
    )
    session.add(rec)
    await session.flush()
    await session.refresh(rec)
    return rec


async def recipient_get_by_token(session: AsyncSession, token: str) -> PhishingRecipient | None:
    result = await session.execute(
        select(PhishingRecipient).where(PhishingRecipient.tracking_token == token)
    )
    return result.scalar_one_or_none()


async def recipient_mark_sent(session: AsyncSession, recipient_id: int) -> None:
    result = await session.execute(select(PhishingRecipient).where(PhishingRecipient.id == recipient_id))
    recipient = result.scalar_one_or_none()
    if recipient:
        recipient.sent_at = datetime.utcnow()
        await session.flush()


async def recipient_increment_open(session: AsyncSession, token: str) -> PhishingRecipient | None:
    recipient = await recipient_get_by_token(session, token)
    if not recipient:
        return None
    recipient.open_count += 1
    if recipient.opened_at is None:
        recipient.opened_at = datetime.utcnow()
    await session.flush()
    await session.refresh(recipient)
    return recipient


async def recipient_increment_click(session: AsyncSession, token: str) -> PhishingRecipient | None:
    recipient = await recipient_get_by_token(session, token)
    if not recipient:
        return None
    recipient.click_count += 1
    if recipient.clicked_at is None:
        recipient.clicked_at = datetime.utcnow()
        campaign = await get_by_id(session, recipient.campaign_id, organization_id=recipient.organization_id)
        if campaign:
            campaign.clicked += 1
    await session.flush()
    await session.refresh(recipient)
    return recipient


async def campaign_increment_sent(session: AsyncSession, campaign_id: int, organization_id: int) -> None:
    campaign = await get_by_id(session, campaign_id, organization_id=organization_id)
    if campaign:
        campaign.sent += 1
        await session.flush()
