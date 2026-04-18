"""Super-admin organization routes and LDAP auth integration."""

import pytest
from httpx import AsyncClient

from core.security import hash_password
from modules.organizations.models import Organization
from modules.users.models import User


@pytest.mark.asyncio
async def test_super_admin_lists_organizations(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["super_admin_email"], ctx["password"], ctx["org_a_id"])
    r = await client.get("/api/organizations", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    names = {o["name"] for o in r.json()}
    assert "Org Alpha Test" in names


@pytest.mark.asyncio
async def test_super_admin_creates_organization(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["super_admin_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        "/api/organizations",
        json={"name": "New Tenant From Test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "New Tenant From Test"


@pytest.mark.asyncio
async def test_super_admin_updates_auth_and_ldap(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["super_admin_email"], ctx["password"], ctx["org_a_id"])

    r = await client.patch(
        f"/api/organizations/{ctx['org_b_id']}/auth-mode",
        json={"authMode": "ldap"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["authMode"] == "ldap"

    r2 = await client.patch(
        f"/api/organizations/{ctx['org_b_id']}/ldap",
        json={
            "ldapServer": "ldap.test.example.com",
            "ldapPort": 636,
            "ldapBaseDn": "dc=test,dc=example,dc=com",
            "ldapBindDn": "cn=admin",
            "ldapBindPassword": "secret",
            "ldapUserFilter": "(uid=%s)",
            "ldapUseSsl": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["ldapServer"] == "ldap.test.example.com"

    r3 = await client.patch(
        f"/api/organizations/{ctx['org_b_id']}/status",
        json={"status": "suspended"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "suspended"


@pytest.mark.asyncio
async def test_regular_admin_forbidden_on_organizations(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.get("/api/organizations", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_login_ldap_mode_uses_provider_mock(
    client: AsyncClient,
    db_session,
    monkeypatch,
):
    """When org auth_mode is ldap, password verification delegates to LDAP provider."""
    org = Organization(
        name="LDAP Org",
        status="active",
        auth_mode="ldap",
        ldap_server="ldap.example.com",
        ldap_port=389,
        ldap_base_dn="dc=example,dc=com",
        ldap_bind_dn="cn=admin,dc=example,dc=com",
        ldap_bind_password="bind-secret",
        ldap_user_filter="(objectClass=person)",
        ldap_use_ssl=False,
    )
    db_session.add(org)
    await db_session.flush()
    pwd_plain = "LdapPass123!"
    u = User(
        organization_id=org.id,
        email="ldap.user@example.com",
        name="LDAP User",
        role="trainee",
        department="IT",
        hashed_password=hash_password("unused-local-hash"),
    )
    db_session.add(u)
    await db_session.commit()

    def _ldap_ok(**kwargs):
        return kwargs.get("password") == pwd_plain

    monkeypatch.setattr("modules.auth.service.authenticate_ldap_user", _ldap_ok)

    r = await client.post(
        "/api/auth/login",
        json={"email": "ldap.user@example.com", "password": pwd_plain, "organizationId": str(org.id)},
    )
    assert r.status_code == 200
    assert r.json().get("success") is True
    assert r.json().get("token")

    r_bad = await client.post(
        "/api/auth/login",
        json={"email": "ldap.user@example.com", "password": "wrong", "organizationId": str(org.id)},
    )
    assert r_bad.json().get("success") is False
