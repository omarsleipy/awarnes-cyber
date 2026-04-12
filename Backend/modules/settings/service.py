import json
from sqlalchemy.ext.asyncio import AsyncSession
from config import get_settings
from modules.settings import repository as repo
from modules.settings.schemas import SmtpConfig, LdapConfig

SETTINGS_SMTP = "smtp_config"
SETTINGS_LDAP = "ldap_config"


def _default_smtp() -> SmtpConfig:
    s = get_settings()
    return SmtpConfig(host=s.SMTP_HOST, port=s.SMTP_PORT, username=s.SMTP_USERNAME, password=s.SMTP_PASSWORD, fromName=s.SMTP_FROM_NAME, fromEmail=s.SMTP_FROM_EMAIL)


def _default_ldap() -> LdapConfig:
    s = get_settings()
    return LdapConfig(server=s.LDAP_SERVER, port=s.LDAP_PORT, baseDn=s.LDAP_BASE_DN, bindDn=s.LDAP_BIND_DN, bindPassword=s.LDAP_BIND_PASSWORD, userFilter=s.LDAP_USER_FILTER, useSsl=s.LDAP_USE_SSL)


async def get_smtp(session: AsyncSession) -> SmtpConfig:
    raw = await repo.get(session, SETTINGS_SMTP)
    if raw:
        try:
            data = json.loads(raw)
            return SmtpConfig(**data)
        except Exception:
            pass
    return _default_smtp()


async def save_smtp(session: AsyncSession, config: SmtpConfig) -> None:
    await repo.set_val(session, SETTINGS_SMTP, config.model_dump_json())


async def get_ldap(session: AsyncSession) -> LdapConfig:
    raw = await repo.get(session, SETTINGS_LDAP)
    if raw:
        try:
            data = json.loads(raw)
            return LdapConfig(**data)
        except Exception:
            pass
    return _default_ldap()


async def save_ldap(session: AsyncSession, config: LdapConfig) -> None:
    await repo.set_val(session, SETTINGS_LDAP, config.model_dump_json())
