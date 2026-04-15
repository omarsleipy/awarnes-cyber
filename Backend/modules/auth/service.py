"""Auth business logic: login, token creation."""
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.ldap_provider import authenticate_ldap_user
from core.security import verify_password, create_access_token
from modules.users.repository import get_all_by_email, get_by_email, update_last_login
from modules.organizations.repository import get_by_id as org_get_by_id


async def login(session: AsyncSession, email: str, password: str, organization_id: str | None = None) -> dict:
    """
    Returns either:
    - {"success": True, "user": {...}, "token": "..."}
    - {"success": False, "error": "..."}
    """
    org_id_int: int | None = None
    if organization_id:
        try:
            org_id_int = int(organization_id)
        except ValueError:
            return {"success": False, "error": "Invalid organization"}

    if org_id_int is None:
        users = await get_all_by_email(session, email)
        if len(users) > 1:
            return {"success": False, "error": "Multiple organizations found. Provide organizationId."}
        user = users[0] if users else None
    else:
        user = await get_by_email(session, email, organization_id=org_id_int)
    if not user:
        return {"success": False, "error": "Invalid credentials"}

    organization = await org_get_by_id(session, user.organization_id)
    if organization and organization.status != "active":
        return {"success": False, "error": "Organization is suspended"}

    auth_mode = organization.auth_mode if organization else "local"
    if user.role == "super_admin":
        auth_mode = "local"

    if auth_mode == "ldap":
        cfg = get_settings()
        ok = authenticate_ldap_user(
            server_host=organization.ldap_server if organization and organization.ldap_server else cfg.LDAP_SERVER,
            server_port=organization.ldap_port if organization else cfg.LDAP_PORT,
            use_ssl=organization.ldap_use_ssl if organization else cfg.LDAP_USE_SSL,
            bind_dn=organization.ldap_bind_dn if organization and organization.ldap_bind_dn else cfg.LDAP_BIND_DN,
            bind_password=organization.ldap_bind_password if organization and organization.ldap_bind_password else cfg.LDAP_BIND_PASSWORD,
            base_dn=organization.ldap_base_dn if organization and organization.ldap_base_dn else cfg.LDAP_BASE_DN,
            user_filter=organization.ldap_user_filter if organization and organization.ldap_user_filter else cfg.LDAP_USER_FILTER,
            login=email,
            password=password,
        )
        if not ok:
            return {"success": False, "error": "Invalid LDAP credentials"}
    elif not verify_password(password, user.hashed_password):
        return {"success": False, "error": "Invalid credentials"}

    if user.status != "active":
        return {"success": False, "error": "Account is suspended"}
    await update_last_login(session, user.id)
    token = create_access_token(
        user.id,
        extra={"email": user.email, "role": user.role, "organization_id": user.organization_id},
    )
    return {
        "success": True,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "status": user.status,
            "completedCourses": user.completed_courses,
            "lastLogin": user.last_login.strftime("%Y-%m-%d") if user.last_login else "Never",
        },
        "token": token,
    }
