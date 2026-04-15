"""Phishing simulation routes."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_organization_id, require_admin
from modules.phishing.schemas import CampaignCreate, CampaignSendRequest
from modules.phishing.service import (
    create_campaign,
    list_campaigns,
    list_template_keys,
    send_campaign,
    track_click,
    track_open,
)

router = APIRouter()

# 1x1 transparent PNG.
TRACKING_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd9\x15\xb9"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@router.get("/campaigns")
async def get_campaigns(
    _: int = Depends(require_admin),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    return await list_campaigns(session, organization_id=organization_id)


@router.get("/templates")
async def get_templates(_: int = Depends(require_admin)):
    return {"templates": list_template_keys()}


@router.post("/campaigns")
async def post_campaign(
    body: CampaignCreate,
    _: int = Depends(require_admin),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    return await create_campaign(session, body, organization_id=organization_id)


@router.post("/campaigns/{campaign_id}/send")
async def post_send_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    body: CampaignSendRequest | None = None,
    _: int = Depends(require_admin),
    organization_id: int = Depends(get_current_organization_id),
):
    try:
        cid = int(campaign_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Campaign not found") from None
    destination_url = body.destinationUrl if body else None
    background_tasks.add_task(send_campaign, cid, organization_id, destination_url)
    return {"success": True, "message": "Campaign queued for delivery"}


@router.get("/track/open/{token}.png")
async def get_track_open(
    token: str,
    session: AsyncSession = Depends(get_db),
):
    await track_open(session, token)
    return Response(content=TRACKING_PIXEL_PNG, media_type="image/png")


@router.get("/track/click/{token}")
async def get_track_click(
    token: str,
    session: AsyncSession = Depends(get_db),
):
    url = await track_click(session, token)
    if not url:
        raise HTTPException(status_code=404, detail="Invalid tracking link")
    return RedirectResponse(url=url)
