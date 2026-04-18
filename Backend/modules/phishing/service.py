from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.database import AsyncSessionLocal
from core.mailer import send_email
from modules.monitoring import repository as activity_repo
from modules.settings.service import get_smtp_for_organization
from modules.phishing import repository as repo
from modules.phishing.schemas import CampaignCreate, CampaignOut
from modules.phishing.models import PhishingRecipient
from modules.users.repository import get_all, get_by_department

logger = logging.getLogger(__name__)

_templates_dir = Path(__file__).resolve().parents[2] / "templates" / "phishing"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_templates_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)

# Active HTML templates (file names without .html)
DEFAULT_TEMPLATE = "outlook_login"
ALLOWED_TEMPLATE_KEYS = frozenset({"outlook_login", "google_security_alert", "hr_policy"})

# Map legacy / UI aliases to template files
_TEMPLATE_ALIASES: dict[str, str] = {
    "microsoft": "outlook_login",
    "password-reset": "outlook_login",
    "it-alert": "google_security_alert",
    "password reset": "outlook_login",
    "google": "google_security_alert",
    "local_bank": "hr_policy",
    "benefits": "hr_policy",
    "exec-request": "hr_policy",
    "outlook": "outlook_login",
    "outlook login": "outlook_login",
    "google security": "google_security_alert",
    "hr": "hr_policy",
    "hr policy": "hr_policy",
    "internal hr": "hr_policy",
}


def _normalize_template(template: str) -> str:
    normalized = (template or "").strip().lower().replace(" ", "_")
    if normalized in ALLOWED_TEMPLATE_KEYS:
        return normalized
    if normalized in _TEMPLATE_ALIASES:
        return _TEMPLATE_ALIASES[normalized]
    if "google" in normalized:
        return "google_security_alert"
    if "hr" in normalized or "policy" in normalized or "benefit" in normalized or "executive" in normalized:
        return "hr_policy"
    if "outlook" in normalized or "microsoft" in normalized or "password" in normalized or "sign" in normalized:
        return "outlook_login"
    return DEFAULT_TEMPLATE


def _build_tracking_urls(token: str) -> tuple[str, str, str]:
    """
    Returns (click_url, pixel_url, credential_submit_url).
    Opaque `token` is the recipient's tracking_token (not the integer DB id, to avoid guessable URLs).
    """
    base = get_settings().APP_BASE_URL.rstrip("/")
    # Primary contract: /api/phishing/track/{token} and /api/phishing/track/{token}/open.png
    click_url = f"{base}/api/phishing/track/{token}"
    pixel_url = f"{base}/api/phishing/track/{token}/open.png"
    credential_url = f"{base}/api/phishing/track/{token}/credential"
    return click_url, pixel_url, credential_url


def _render_template(
    *,
    template_key: str,
    full_name: str,
    campaign_name: str,
    click_url: str,
    pixel_url: str,
    credential_url: str,
) -> str:
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
        credential_url=credential_url,
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


async def _record_phishing_activity(
    session: AsyncSession,
    *,
    recipient: PhishingRecipient,
    activity_type: str,
    title: str,
    severity: str = "warning",
    details: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    await activity_repo.create(
        session,
        organization_id=recipient.organization_id,
        user_id=recipient.user_id,
        activity_type=activity_type,
        title=title,
        severity=severity,
        details=details,
        ip=ip_address,
        user_agent=user_agent,
        exam_id=None,
        phishing_campaign_id=recipient.campaign_id,
        phishing_recipient_id=recipient.id,
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
        smtp_cfg = await get_smtp_for_organization(session, organization_id)
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
            click_url, pixel_url, credential_url = _build_tracking_urls(token)
            html = _render_template(
                template_key=template_key,
                full_name=user.name,
                campaign_name=campaign.name,
                click_url=click_url,
                pixel_url=pixel_url,
                credential_url=credential_url,
            )
            try:
                await send_email(
                    to_email=user.email,
                    subject=f"Action required: {campaign.name}",
                    html=html,
                    text=f"Hi {user.name}, review this message: {click_url}",
                    smtp_config=smtp_cfg,
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


async def track_open(
    session: AsyncSession,
    token: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> bool:
    recipient = await repo.recipient_increment_open(session, token)
    if not recipient:
        return False
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    await _record_phishing_activity(
        session,
        recipient=recipient,
        activity_type="phishing_tracking_pixel_opened",
        title="Phishing simulation: tracking pixel loaded (email/attachment viewed)",
        severity="warning",
        details=f"Opened at {ts}. Recipient email: {recipient.email}. Simulated attachment/email open tracking.",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return True


async def track_click(
    session: AsyncSession,
    token: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> PhishingRecipient | None:
    recipient = await repo.recipient_increment_click(session, token)
    if not recipient:
        return None
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    await _record_phishing_activity(
        session,
        recipient=recipient,
        activity_type="phishing_link_clicked",
        title="Phishing simulation: malicious link clicked",
        severity="critical",
        details=f"Clicked at {ts}. Destination after redirect is the configured safe URL (training). Recipient: {recipient.email}.",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return recipient


async def track_credential_submit(
    session: AsyncSession,
    token: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
    username_hint: str | None = None,
) -> PhishingRecipient | None:
    """Logs a simulated credential submission (training). Does not persist passwords."""
    recipient = await repo.recipient_get_by_token(session, token)
    if not recipient:
        return None
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    hint = ""
    if username_hint:
        hint = f" Username field present (partially redacted): {username_hint[:2]}***."
    await _record_phishing_activity(
        session,
        recipient=recipient,
        activity_type="phishing_credentials_submitted",
        title="Phishing simulation: credentials submitted on fake page",
        severity="critical",
        details=f"Submitted at {ts}.{hint} Password value is never stored (training simulation only). Recipient: {recipient.email}.",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.flush()
    return recipient
