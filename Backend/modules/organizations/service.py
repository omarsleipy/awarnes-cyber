"""Organization admin service."""
from sqlalchemy.ext.asyncio import AsyncSession

from modules.organizations import repository as repo
from modules.organizations.schemas import OrganizationOut


def _out(org) -> OrganizationOut:
    return OrganizationOut(
        id=str(org.id),
        name=org.name,
        status=org.status,
        authMode=org.auth_mode,
    )


async def list_organizations(session: AsyncSession) -> list[OrganizationOut]:
    rows = await repo.list_all(session)
    return [_out(org) for org in rows]


async def create_organization(session: AsyncSession, name: str) -> OrganizationOut:
    existing = await repo.get_by_name(session, name.strip())
    if existing:
        return _out(existing)
    org = await repo.create(session, name=name.strip())
    return _out(org)


async def set_auth_mode(session: AsyncSession, organization_id: int, auth_mode: str) -> OrganizationOut | None:
    org = await repo.get_by_id(session, organization_id)
    if not org:
        return None
    mode = (auth_mode or "").strip().lower()
    if mode not in {"local", "ldap"}:
        mode = "local"
    org.auth_mode = mode
    await session.flush()
    await session.refresh(org)
    return _out(org)


async def set_status(session: AsyncSession, organization_id: int, status: str) -> OrganizationOut | None:
    org = await repo.get_by_id(session, organization_id)
    if not org:
        return None
    val = (status or "").strip().lower()
    if val not in {"active", "suspended"}:
        val = "active"
    org.status = val
    await session.flush()
    await session.refresh(org)
    return _out(org)


async def set_ldap_config(
    session: AsyncSession,
    organization_id: int,
    *,
    ldap_server: str,
    ldap_port: int,
    ldap_base_dn: str,
    ldap_bind_dn: str,
    ldap_bind_password: str,
    ldap_user_filter: str,
    ldap_use_ssl: bool,
) -> OrganizationOut | None:
    org = await repo.get_by_id(session, organization_id)
    if not org:
        return None
    org.ldap_server = ldap_server
    org.ldap_port = ldap_port
    org.ldap_base_dn = ldap_base_dn
    org.ldap_bind_dn = ldap_bind_dn
    org.ldap_bind_password = ldap_bind_password
    org.ldap_user_filter = ldap_user_filter
    org.ldap_use_ssl = ldap_use_ssl
    await session.flush()
    await session.refresh(org)
    return _out(org)

