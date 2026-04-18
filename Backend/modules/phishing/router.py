"""Phishing simulation routes."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
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
    track_credential_submit,
    track_open,
)

router = APIRouter()

# 1x1 transparent PNG.
TRACKING_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd9\x15\xb9"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = None
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        ip = xff.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    ua = request.headers.get("user-agent")
    return ip, ua


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


# --- Tracking: primary URLs use opaque token (same as phishing_recipients.tracking_token). ---


@router.get("/track/{token}/open.png")
async def get_track_open_png(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    ip, ua = _client_meta(request)
    await track_open(session, token, ip_address=ip, user_agent=ua)
    return Response(content=TRACKING_PIXEL_PNG, media_type="image/png")


@router.post("/track/{token}/credential")
async def post_track_credential(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Simulated credential harvest (training). Password is never stored."""
    form = await request.form()
    username = (form.get("username") or form.get("email") or "") if form else ""
    username_str = str(username).strip()[:200] if username else None
    ip, ua = _client_meta(request)
    recipient = await track_credential_submit(session, token, ip_address=ip, user_agent=ua, username_hint=username_str)
    if not recipient:
        raise HTTPException(status_code=404, detail="Invalid tracking link") from None
    # Simple acknowledgment page (no secrets)
    return HTMLResponse(
        content="<html><body style='font-family:system-ui;padding:2rem'>"
        "<p>This was a <strong>simulated phishing exercise</strong>. No credentials were stored.</p>"
        "<p>You may close this window.</p></body></html>",
        status_code=200,
    )


@router.get("/track/{token}")
async def get_track_click_primary(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    ip, ua = _client_meta(request)
    recipient = await track_click(session, token, ip_address=ip, user_agent=ua)
    if not recipient:
        raise HTTPException(status_code=404, detail="Invalid tracking link") from None
    return RedirectResponse(url=recipient.destination_url)


# --- Legacy tracking URLs (still supported for older sent emails) ---


@router.get("/track/open/{token}.png")
async def get_track_open_legacy(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    ip, ua = _client_meta(request)
    await track_open(session, token, ip_address=ip, user_agent=ua)
    return Response(content=TRACKING_PIXEL_PNG, media_type="image/png")


@router.get("/track/click/{token}")
async def get_track_click_legacy(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    ip, ua = _client_meta(request)
    recipient = await track_click(session, token, ip_address=ip, user_agent=ua)
    if not recipient:
        raise HTTPException(status_code=404, detail="Invalid tracking link") from None
    return RedirectResponse(url=recipient.destination_url)
