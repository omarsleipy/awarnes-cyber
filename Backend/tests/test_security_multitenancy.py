"""JWT, RBAC, and multi-tenant isolation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_users_route_requires_authentication(client: AsyncClient):
    r = await client.get("/api/users")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_jwt_login_and_protected_route(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])

    r = await client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    # Only users in Org Alpha
    emails = {u["email"] for u in body}
    assert ctx["admin_a_email"] in emails
    assert ctx["admin_b_email"] not in emails


@pytest.mark.asyncio
async def test_trainee_cannot_access_admin_phishing(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])

    r = await client.get("/api/phishing/campaigns", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_org_b_cannot_see_org_a_campaigns(
    client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session
):
    """Campaigns created in Org A must not appear when authenticated as Org B admin."""
    from modules.phishing.models import PhishingCampaign

    ctx = two_orgs_with_users
    # Seed a campaign directly for Org A
    camp = PhishingCampaign(
        organization_id=ctx["org_a_id"],
        name="Secret Alpha Campaign",
        template="outlook_login",
        target_dept="All",
        sent=0,
        clicked=0,
        reported=0,
        status="draft",
    )
    db_session.add(camp)
    await db_session.commit()

    token_b = await login_helper(ctx["admin_b_email"], ctx["password"], ctx["org_b_id"])
    r = await client.get("/api/phishing/campaigns", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    names = {c["name"] for c in r.json()}
    assert "Secret Alpha Campaign" not in names


@pytest.mark.asyncio
async def test_org_b_monitoring_events_isolated(client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session):
    """SuspiciousActivity rows scoped to Org A must not appear in Org B monitoring list."""
    from modules.monitoring.repository import create as log_activity

    ctx = two_orgs_with_users
    await log_activity(
        db_session,
        organization_id=ctx["org_a_id"],
        user_id=None,
        activity_type="test_event",
        title="Alpha only event",
        severity="warning",
        details="secret",
        ip="10.0.0.1",
        user_agent="pytest",
        exam_id=None,
        phishing_campaign_id=None,
        phishing_recipient_id=None,
    )
    await db_session.commit()

    token_b = await login_helper(ctx["admin_b_email"], ctx["password"], ctx["org_b_id"])
    r = await client.get("/api/monitoring/activities", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    titles = {row["title"] for row in r.json()}
    assert "Alpha only event" not in titles


@pytest.mark.asyncio
async def test_per_organization_smtp_keys_are_isolated_in_db(two_orgs_with_users: dict, db_session):
    """Outbound SMTP for phishing uses `smtp_config_org_{id}` — org A must not read org B's host."""
    from modules.settings.schemas import SmtpConfig
    from modules.settings.service import get_smtp_for_organization, save_smtp_for_organization

    ctx = two_orgs_with_users
    await save_smtp_for_organization(
        db_session,
        ctx["org_a_id"],
        SmtpConfig(host="smtp.org-a.example", port=587, encryption="TLS"),
    )
    await save_smtp_for_organization(
        db_session,
        ctx["org_b_id"],
        SmtpConfig(host="smtp.org-b.example", port=587, encryption="TLS"),
    )
    await db_session.commit()

    a = await get_smtp_for_organization(db_session, ctx["org_a_id"])
    b = await get_smtp_for_organization(db_session, ctx["org_b_id"])
    assert a.host == "smtp.org-a.example"
    assert b.host == "smtp.org-b.example"
