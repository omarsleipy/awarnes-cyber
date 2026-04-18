"""Monitoring business logic: log and list suspicious activities."""
from sqlalchemy.ext.asyncio import AsyncSession

from modules.monitoring import repository as repo
from modules.monitoring.schemas import ActivityCreate, ActivityResponse


def _to_response(a) -> ActivityResponse:
    return ActivityResponse(
        id=str(a.id),
        organization_id=str(a.organization_id) if getattr(a, "organization_id", None) is not None else None,
        user_id=str(a.user_id) if a.user_id is not None else None,
        activity_type=a.activity_type,
        severity=a.severity,
        title=a.title,
        details=a.details,
        ip_address=a.ip_address,
        exam_id=a.exam_id,
        phishing_campaign_id=str(a.phishing_campaign_id) if getattr(a, "phishing_campaign_id", None) is not None else None,
        phishing_recipient_id=str(a.phishing_recipient_id) if getattr(a, "phishing_recipient_id", None) is not None else None,
        created_at=a.created_at.isoformat() if a.created_at else "",
    )


async def log_activity(session: AsyncSession, user_id: int | None, payload: ActivityCreate, ip: str | None = None, user_agent: str | None = None) -> ActivityResponse:
    a = await repo.create(
        session,
        organization_id=None,
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


async def list_activities_for_org(session: AsyncSession, *, organization_id: int, limit: int = 200) -> list[ActivityResponse]:
    activities = await repo.list_for_organization(session, organization_id=organization_id, limit=limit)
    return [_to_response(a) for a in activities]
