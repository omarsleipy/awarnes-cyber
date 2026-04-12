"""SMTP / LDAP settings (stored in DB, tests are stubs)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import require_admin
from modules.settings.schemas import LdapConfig, SmtpConfig
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
async def smtp_test(_: int = Depends(require_admin)):
    return {"success": True, "message": "Test email sent (stub)"}


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
