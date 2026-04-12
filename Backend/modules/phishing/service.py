from sqlalchemy.ext.asyncio import AsyncSession

from modules.phishing import repository as repo
from modules.phishing.schemas import CampaignCreate, CampaignOut


def _out(c) -> CampaignOut:
    return CampaignOut(
        id=str(c.id),
        name=c.name,
        template=c.template,
        targetDept=c.target_dept,
        sent=c.sent,
        clicked=c.clicked,
        reported=c.reported,
        status=c.status,
        createdAt=c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
    )


async def list_campaigns(session: AsyncSession) -> list[CampaignOut]:
    rows = await repo.list_all(session)
    return [_out(c) for c in rows]


async def create_campaign(session: AsyncSession, payload: CampaignCreate) -> CampaignOut:
    name = (payload.name or "").strip() or "Untitled campaign"
    c = await repo.create(session, name=name, template=payload.template, target_dept=payload.targetDept)
    return _out(c)
