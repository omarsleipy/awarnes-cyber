"""Phishing simulation routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import require_admin
from modules.phishing.schemas import CampaignCreate
from modules.phishing.service import create_campaign, list_campaigns

router = APIRouter()


@router.get("/campaigns")
async def get_campaigns(
    _: int = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    return await list_campaigns(session)


@router.post("/campaigns")
async def post_campaign(
    body: CampaignCreate,
    _: int = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    return await create_campaign(session, body)
