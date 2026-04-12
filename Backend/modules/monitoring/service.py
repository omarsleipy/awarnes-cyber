"""Monitoring business logic: log and list suspicious activities."""
from sqlalchemy.ext.asyncio import AsyncSession

from modules.monitoring import repository as repo
from modules.monitoring.schemas import ActivityCreate, ActivityResponse


def _to_response(a) -> ActivityResponse:
    return ActivityResponse(
        id=str(a.id),
        user_id=str(a.user_id) if a.user_id is not None else None,
        activity_type=a.activity_type,
        severity=a.severity,
        title=a.title,
        details=a.details,
        ip_address=a.ip_address,
        exam_id=a.exam_id,
        created_at=a.created_at.isoformat() if a.created_at else "",
    )


async def log_activity(session: AsyncSession, user_id: int | None, payload: ActivityCreate, ip: str | None = None, user_agent: str | None = None) -> ActivityResponse:
    a = await repo.create(
        session,
        user_id=user_id,
        activity_type=payload.activity_type,
        title=payload.title,
        severity=payload.severity,
        details=payload.details,
        ip=ip,
        user_agent=user_agent,
        exam_id=payload.exam_id,
    )
    return _to_response(a)


async def list_activities(session: AsyncSession, limit: int = 100, severity: str | None = None) -> list[ActivityResponse]:
    activities = await repo.list_recent(session, limit=limit, severity=severity)
    return [_to_response(a) for a in activities]
