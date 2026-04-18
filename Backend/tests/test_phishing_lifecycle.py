"""Phishing campaigns, templates, and tracking (pixel / click / credential)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import AsyncSessionLocal


@pytest.mark.parametrize(
    "template_key",
    ["outlook_login", "google_security_alert", "hr_policy"],
)
@pytest.mark.asyncio
async def test_create_campaign_accepts_templates(
    client: AsyncClient,
    two_orgs_with_users: dict,
    login_helper,
    template_key: str,
):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        "/api/phishing/campaigns",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"Campaign {template_key}", "template": template_key, "targetDept": "All"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["template"] == template_key


@pytest.mark.asyncio
async def test_tracking_pixel_records_suspicious_activity(
    client: AsyncClient,
    two_orgs_with_users: dict,
    db_session,
):
    from modules.monitoring.models import SuspiciousActivity
    from modules.phishing import repository as ph_repo

    ctx = two_orgs_with_users
    camp = await ph_repo.create(
        db_session,
        organization_id=ctx["org_a_id"],
        name="Track test",
        template="outlook_login",
        target_dept="All",
    )
    await ph_repo.recipient_create(
        db_session,
        organization_id=ctx["org_a_id"],
        campaign_id=camp.id,
        user_id=ctx["admin_a_user_id"],
        email=ctx["admin_a_email"],
        destination_url="https://training.example/safe",
        tracking_token="pytest-pixel-token-001",
    )
    await db_session.commit()

    r = await client.get(
        "/api/phishing/track/pytest-pixel-token-001/open.png",
        headers={"User-Agent": "pytest-ua"},
    )
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/png")

    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(SuspiciousActivity).where(
                SuspiciousActivity.activity_type == "phishing_tracking_pixel_opened",
                SuspiciousActivity.organization_id == ctx["org_a_id"],
            )
        )
        rows = q.scalars().all()
    assert len(rows) >= 1
    assert rows[-1].user_agent == "pytest-ua"


@pytest.mark.asyncio
async def test_tracking_click_redirects_and_logs(
    client: AsyncClient,
    two_orgs_with_users: dict,
):
    from modules.monitoring.models import SuspiciousActivity
    from modules.phishing import repository as ph_repo

    ctx = two_orgs_with_users
    async with AsyncSessionLocal() as session:
        camp = await ph_repo.create(
            session,
            organization_id=ctx["org_a_id"],
            name="Click test",
            template="google_security_alert",
            target_dept="All",
        )
        await ph_repo.recipient_create(
            session,
            organization_id=ctx["org_a_id"],
            campaign_id=camp.id,
            user_id=ctx["admin_a_user_id"],
            email=ctx["admin_a_email"],
            destination_url="https://redirect.example/post-click",
            tracking_token="pytest-click-token-002",
        )
        await session.commit()

    r = await client.get(
        "/api/phishing/track/pytest-click-token-002",
        follow_redirects=False,
    )
    assert r.status_code in (307, 302)
    assert r.headers["location"] == "https://redirect.example/post-click"

    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(SuspiciousActivity).where(
                SuspiciousActivity.activity_type == "phishing_link_clicked",
                SuspiciousActivity.organization_id == ctx["org_a_id"],
            )
        )
        rows = q.scalars().all()
    assert rows


@pytest.mark.asyncio
async def test_credential_submit_logs_without_password_plaintext(
    client: AsyncClient,
    two_orgs_with_users: dict,
):
    from modules.monitoring.models import SuspiciousActivity
    from modules.phishing import repository as ph_repo

    ctx = two_orgs_with_users
    secret_pw = "NEVER_PERSIST_THIS_VALUE_99284"
    async with AsyncSessionLocal() as session:
        camp = await ph_repo.create(
            session,
            organization_id=ctx["org_a_id"],
            name="Cred test",
            template="hr_policy",
            target_dept="All",
        )
        await ph_repo.recipient_create(
            session,
            organization_id=ctx["org_a_id"],
            campaign_id=camp.id,
            user_id=ctx["admin_a_user_id"],
            email=ctx["admin_a_email"],
            destination_url="https://training.example/safe",
            tracking_token="pytest-cred-token-003",
        )
        await session.commit()

    r = await client.post(
        "/api/phishing/track/pytest-cred-token-003/credential",
        data={"username": "fake.user@example.com", "password": secret_pw},
        headers={"User-Agent": "pytest-cred-ua"},
    )
    assert r.status_code == 200
    assert "no credentials were stored" in r.text.lower()

    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(SuspiciousActivity)
            .where(SuspiciousActivity.activity_type == "phishing_credentials_submitted")
            .order_by(SuspiciousActivity.id.desc())
            .limit(5)
        )
        rows = q.scalars().all()
    assert rows
    details_blob = " ".join((x.details or "") for x in rows)
    assert secret_pw not in details_blob
