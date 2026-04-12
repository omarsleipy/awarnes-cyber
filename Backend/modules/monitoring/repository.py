"""Database queries for suspicious activities."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.monitoring.models import SuspiciousActivity


async def create(session: AsyncSession, user_id: int | None, activity_type: str, title: str, severity: str = "warning", details: str | None = None, ip: str | None = None, user_agent: str | None = None, exam_id: int | None = None) -> SuspiciousActivity:
    a = SuspiciousActivity(
        user_id=user_id,
        activity_type=activity_type,
        title=title,
        severity=severity,
        details=details,
        ip_address=ip,
        user_agent=user_agent,
        exam_id=exam_id,
    )
    session.add(a)
    await session.flush()
    await session.refresh(a)
    return a


async def list_recent(session: AsyncSession, limit: int = 100, severity: str | None = None) -> list[SuspiciousActivity]:
    q = select(SuspiciousActivity).order_by(SuspiciousActivity.created_at.desc()).limit(limit)
    if severity:
        q = q.where(SuspiciousActivity.severity == severity)
    result = await session.execute(q)
    return list(result.scalars().all())
