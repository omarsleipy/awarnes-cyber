from __future__ import annotations

import logging
import secrets
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.database import AsyncSessionLocal
from core.mailer import send_email
from modules.phishing import repository as repo
from modules.phishing.schemas import CampaignCreate, CampaignOut
from modules.users.repository import get_all, get_by_department

logger = logging.getLogger(__name__)

_templates_dir = Path(__file__).resolve().parents[2] / "templates" / "phishing"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_templates_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)

DEFAULT_TEMPLATE = "microsoft"
ALLOWED_TEMPLATE_KEYS = {"microsoft", "google", "local_bank"}


def _normalize_template(template: str) -> str:
    normalized = (template or "").strip().lower().replace(" ", "_")
    if normalized in ALLOWED_TEMPLATE_KEYS:
        return normalized
    if "google" in normalized:
        return "google"
    if "bank" in normalized:
        return "local_bank"
    if "microsoft" in normalized or "password" in normalized:
        return "microsoft"
    return DEFAULT_TEMPLATE


def _build_tracking_urls(token: str) -> tuple[str, str]:
    base_url = get_settings().APP_BASE_URL.rstrip("/")
    pixel_url = f"{base_url}/api/phishing/track/open/{token}.png"
    click_url = f"{base_url}/api/phishing/track/click/{token}"
    return pixel_url, click_url


def _render_template(*, template_key: str, full_name: str, campaign_name: str, click_url: str, pixel_url: str) -> str:
    template_name = f"{template_key}.html"
    try:
        template = _jinja_env.get_template(template_name)
    except TemplateNotFound:
        template = _jinja_env.get_template(f"{DEFAULT_TEMPLATE}.html")
    return template.render(
        full_name=full_name,
        campaign_name=campaign_name,
        click_url=click_url,
        pixel_url=pixel_url,
    )


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


async def list_campaigns(session: AsyncSession, organization_id: int) -> list[CampaignOut]:
    rows = await repo.list_all(session, organization_id=organization_id)
    return [_out(c) for c in rows]


def list_template_keys() -> list[str]:
    return sorted(ALLOWED_TEMPLATE_KEYS)


async def create_campaign(session: AsyncSession, payload: CampaignCreate, organization_id: int) -> CampaignOut:
    name = (payload.name or "").strip() or "Untitled campaign"
    c = await repo.create(
        session,
        organization_id=organization_id,
        name=name,
        template=_normalize_template(payload.template),
        target_dept=payload.targetDept,
    )
    return _out(c)


async def send_campaign(campaign_id: int, organization_id: int, destination_url: str | None = None) -> None:
    """Background-safe campaign sender using its own DB session."""
    async with AsyncSessionLocal() as session:
        campaign = await repo.get_by_id(session, campaign_id, organization_id=organization_id)
        if not campaign:
            logger.warning("Phishing campaign %s not found", campaign_id)
            return

        await repo.update_status(session, campaign_id, "active", organization_id=organization_id)

        if campaign.target_dept.lower() == "all":
            users = await get_all(session, organization_id=organization_id, skip=0, limit=5000)
        else:
            users = await get_by_department(session, organization_id=organization_id, department=campaign.target_dept)

        template_key = _normalize_template(campaign.template)
        target_url = destination_url or "https://example.com"
        sent_count = 0
        for user in users:
            token = secrets.token_urlsafe(24)
            recipient = await repo.recipient_create(
                session,
                organization_id=organization_id,
                campaign_id=campaign.id,
                user_id=user.id,
                email=user.email,
                destination_url=target_url,
                tracking_token=token,
            )
            pixel_url, click_url = _build_tracking_urls(token)
            html = _render_template(
                template_key=template_key,
                full_name=user.name,
                campaign_name=campaign.name,
                click_url=click_url,
                pixel_url=pixel_url,
            )
            try:
                await send_email(
                    to_email=user.email,
                    subject=f"Action required: {campaign.name}",
                    html=html,
                    text=f"Hi {user.name}, review this message: {click_url}",
                )
                await repo.recipient_mark_sent(session, recipient.id)
                await repo.campaign_increment_sent(session, campaign.id, organization_id=organization_id)
                sent_count += 1
            except Exception:
                logger.exception(
                    "Failed to send phishing mail for campaign=%s to user=%s",
                    campaign.id,
                    user.email,
                )

        await repo.update_status(
            session,
            campaign_id,
            "completed" if sent_count else "draft",
            organization_id=organization_id,
        )
        await session.commit()


async def track_open(session: AsyncSession, token: str) -> bool:
    return (await repo.recipient_increment_open(session, token)) is not None


async def track_click(session: AsyncSession, token: str) -> str | None:
    recipient = await repo.recipient_increment_click(session, token)
    if not recipient:
        return None
    return recipient.destination_url
