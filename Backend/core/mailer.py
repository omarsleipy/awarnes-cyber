"""SMTP email delivery service with optional mock mode."""
from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from config import get_settings
from modules.settings.schemas import SmtpConfig

logger = logging.getLogger(__name__)


def _build_sender() -> str:
    s = get_settings()
    display_name = (s.SMTP_FROM_NAME or "").strip()
    email = (s.SMTP_FROM_EMAIL or "").strip()
    if display_name:
        return f"{display_name} <{email}>"
    return email


def _build_sender_from_smtp(smtp: SmtpConfig) -> str:
    display_name = (smtp.fromName or "").strip()
    email = (smtp.fromEmail or "").strip() or get_settings().SMTP_FROM_EMAIL
    if display_name:
        return f"{display_name} <{email}>"
    return email


async def send_email(
    *,
    to_email: str,
    subject: str,
    html: str,
    text: str | None = None,
    smtp_config: SmtpConfig | None = None,
) -> None:
    """
    Send an email via SMTP, or log it when SMTP_MOCK_MODE is enabled.
    If `smtp_config` is provided and has a host, that host is used (e.g. per-organization settings);
    otherwise environment / global defaults apply.
    """
    s = get_settings()

    if s.SMTP_MOCK_MODE:
        host_hint = (smtp_config.host if smtp_config and smtp_config.host else s.SMTP_HOST) or "mock"
        logger.info(
            "[SMTP MOCK] to=%s subject=%s smtp_host=%s text=%s",
            to_email,
            subject,
            host_hint,
            (text or "")[:200],
        )
        return

    msg = EmailMessage()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(text or "This email requires HTML support.")
    msg.add_alternative(html, subtype="html")

    if smtp_config and (smtp_config.host or "").strip():
        sc = smtp_config
        msg["From"] = _build_sender_from_smtp(sc)
        enc = (sc.encryption or "TLS").upper()
        use_tls = enc in ("TLS", "STARTTLS", "")
        await aiosmtplib.send(
            msg,
            hostname=sc.host,
            port=sc.port or 587,
            username=sc.username or None,
            password=sc.password or None,
            start_tls=use_tls,
        )
        return

    if not s.SMTP_HOST:
        raise ValueError("SMTP_HOST is required when SMTP_MOCK_MODE is disabled and no smtp_config.host is set")

    msg["From"] = _build_sender()
    await aiosmtplib.send(
        msg,
        hostname=s.SMTP_HOST,
        port=s.SMTP_PORT,
        username=s.SMTP_USERNAME or None,
        password=s.SMTP_PASSWORD or None,
        start_tls=s.SMTP_USE_TLS,
    )

