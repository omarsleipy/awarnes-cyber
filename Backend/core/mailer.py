"""SMTP email delivery service with optional mock mode."""
from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from config import get_settings

logger = logging.getLogger(__name__)


def _build_sender() -> str:
    s = get_settings()
    display_name = (s.SMTP_FROM_NAME or "").strip()
    email = (s.SMTP_FROM_EMAIL or "").strip()
    if display_name:
        return f"{display_name} <{email}>"
    return email


async def send_email(*, to_email: str, subject: str, html: str, text: str | None = None) -> None:
    """Send an email via SMTP, or log it when SMTP_MOCK_MODE is enabled."""
    s = get_settings()

    if s.SMTP_MOCK_MODE:
        logger.info(
            "[SMTP MOCK] to=%s subject=%s text=%s html=%s",
            to_email,
            subject,
            text or "",
            html,
        )
        return

    if not s.SMTP_HOST:
        raise ValueError("SMTP_HOST is required when SMTP_MOCK_MODE is disabled")

    msg = EmailMessage()
    msg["From"] = _build_sender()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(text or "This email requires HTML support.")
    msg.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=s.SMTP_HOST,
        port=s.SMTP_PORT,
        username=s.SMTP_USERNAME or None,
        password=s.SMTP_PASSWORD or None,
        start_tls=s.SMTP_USE_TLS,
    )

