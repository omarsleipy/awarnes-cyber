"""Organization management routes (super admin)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import require_super_admin
from modules.organizations.schemas import (
    OrganizationAuthUpdateRequest,
    OrganizationCreateRequest,
    OrganizationLdapConfigRequest,
    OrganizationStatusUpdateRequest,
)
from modules.organizations import service

router = APIRouter()


@router.get("")
async def get_organizations(
    _: int = Depends(require_super_admin),
    session: AsyncSession = Depends(get_db),
):
    return [org.model_dump() for org in await service.list_organizations(session)]


@router.post("")
async def post_organization(
    body: OrganizationCreateRequest,
    _: int = Depends(require_super_admin),
    session: AsyncSession = Depends(get_db),
):
    created = await service.create_organization(session, body.name)
    return created.model_dump()


@router.patch("/{organization_id}/auth-mode")
async def patch_auth_mode(
    organization_id: str,
    body: OrganizationAuthUpdateRequest,
    _: int = Depends(require_super_admin),
    session: AsyncSession = Depends(get_db),
):
    try:
        oid = int(organization_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Organization not found") from None
    row = await service.set_auth_mode(session, oid, body.authMode)
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    return row.model_dump()


@router.patch("/{organization_id}/status")
async def patch_status(
    organization_id: str,
    body: OrganizationStatusUpdateRequest,
    _: int = Depends(require_super_admin),
    session: AsyncSession = Depends(get_db),
):
    try:
        oid = int(organization_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Organization not found") from None
    row = await service.set_status(session, oid, body.status)
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    return row.model_dump()


@router.patch("/{organization_id}/ldap")
async def patch_ldap(
    organization_id: str,
    body: OrganizationLdapConfigRequest,
    _: int = Depends(require_super_admin),
    session: AsyncSession = Depends(get_db),
):
    try:
        oid = int(organization_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Organization not found") from None
    row = await service.set_ldap_config(
        session,
        oid,
        ldap_server=body.ldapServer,
        ldap_port=body.ldapPort,
        ldap_base_dn=body.ldapBaseDn,
        ldap_bind_dn=body.ldapBindDn,
        ldap_bind_password=body.ldapBindPassword,
        ldap_user_filter=body.ldapUserFilter,
        ldap_use_ssl=body.ldapUseSsl,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    return row.model_dump()

