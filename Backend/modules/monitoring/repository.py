"""Database queries for suspicious activities."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.monitoring.models import SuspiciousActivity


async def create(
    session: AsyncSession,
    *,
    organization_id: int | None,
    user_id: int | None,
    activity_type: str,
    title: str,
    severity: str = "warning",
    details: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    exam_id: int | None = None,
    phishing_campaign_id: int | None = None,
    phishing_recipient_id: int | None = None,
) -> SuspiciousActivity:
    a = SuspiciousActivity(
        organization_id=organization_id,
        user_id=user_id,
        activity_type=activity_type,
        title=title,
        severity=severity,
        details=details,
        ip_address=ip,
        user_agent=user_agent,
        exam_id=exam_id,
        phishing_campaign_id=phishing_campaign_id,
        phishing_recipient_id=phishing_recipient_id,
    )
    session.add(a)
    await session.flush()
    await session.refresh(a)
    return a


async def list_for_organization(
    session: AsyncSession,
    *,
    organization_id: int,
    limit: int = 200,
    severity: str | None = None,
) -> list[SuspiciousActivity]:
    stmt = select(SuspiciousActivity).where(SuspiciousActivity.organization_id == organization_id)
    if severity:
        stmt = stmt.where(SuspiciousActivity.severity == severity)
    stmt = stmt.order_by(SuspiciousActivity.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_recent(session: AsyncSession, limit: int = 100, severity: str | None = None) -> list[SuspiciousActivity]:
    """Legacy: all activities (avoid for tenant APIs)."""
    q = select(SuspiciousActivity).order_by(SuspiciousActivity.created_at.desc()).limit(limit)
    if severity:
        q = q.where(SuspiciousActivity.severity == severity)
    result = await session.execute(q)
    return list(result.scalars().all())
