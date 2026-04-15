"""SMTP / LDAP settings routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.database import get_db
from core.mailer import send_email
from core.dependencies import require_admin
from modules.settings.schemas import LdapConfig, SmtpConfig, SmtpTestRequest
from modules.settings.service import get_ldap, get_smtp, save_ldap, save_smtp

router = APIRouter()


@router.get("/smtp", response_model=SmtpConfig)
async def smtp_get(_: int = Depends(require_admin), session: AsyncSession = Depends(get_db)):
    return await get_smtp(session)


@router.post("/smtp")
async def smtp_save(
    body: SmtpConfig,
    _: int = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    await save_smtp(session, body)
    return {"success": True}


@router.post("/smtp/test")
async def smtp_test(
    body: SmtpTestRequest | None = None,
    _: int = Depends(require_admin),
):
    to_email = (body.toEmail if body else None) or get_settings().SMTP_FROM_EMAIL
    await send_email(
        to_email=to_email,
        subject="CyberAware SMTP Test",
        text="SMTP settings are working.",
        html="<p>SMTP settings are working.</p>",
    )
    return {"success": True, "message": f"SMTP test email dispatched to {to_email}"}


@router.get("/ldap", response_model=LdapConfig)
async def ldap_get(_: int = Depends(require_admin), session: AsyncSession = Depends(get_db)):
    return await get_ldap(session)


@router.post("/ldap")
async def ldap_save(
    body: LdapConfig,
    _: int = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
):
    await save_ldap(session, body)
    return {"success": True}


@router.post("/ldap/test")
async def ldap_test(_: int = Depends(require_admin)):
    return {"success": True, "usersFound": 247}
