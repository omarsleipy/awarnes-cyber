"""Monitoring / suspicious activity routes (organization-scoped)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_organization_id, require_admin
from modules.monitoring.service import list_activities_for_org

router = APIRouter()


@router.get("/activities")
async def get_activities(
    _: int = Depends(require_admin),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
    limit: int = 200,
):
    """Suspicious activities for the current organization only (includes phishing simulation events)."""
    return await list_activities_for_org(session, organization_id=organization_id, limit=limit)
