"""Per-organization SMTP resolution and mailer behavior."""

import pytest

from config import get_settings


@pytest.mark.asyncio
async def test_send_campaign_uses_organization_smtp_host_from_db(
    two_orgs_with_users: dict,
    db_session,
    mock_aiosmtplib_send,
):
    from modules.phishing import repository as ph_repo
    from modules.phishing.service import send_campaign
    from modules.settings.schemas import SmtpConfig
    from modules.settings.service import save_smtp_for_organization

    ctx = two_orgs_with_users
    await save_smtp_for_organization(
        db_session,
        ctx["org_a_id"],
        SmtpConfig(host="smtp.alpha.test", port=587, encryption="TLS", fromEmail="a@test.local"),
    )
    await save_smtp_for_organization(
        db_session,
        ctx["org_b_id"],
        SmtpConfig(host="smtp.beta.test", port=587, encryption="TLS", fromEmail="b@test.local"),
    )
    await db_session.commit()

    camp_a = await ph_repo.create(
        db_session,
        organization_id=ctx["org_a_id"],
        name="SMTP org A",
        template="outlook_login",
        target_dept="All",
    )
    await db_session.commit()

    await send_campaign(camp_a.id, ctx["org_a_id"], destination_url="https://safe.example/a")

    assert mock_aiosmtplib_send.await_count >= 1
    hosts_alpha = {call.kwargs.get("hostname") for call in mock_aiosmtplib_send.await_args_list}
    assert "smtp.alpha.test" in hosts_alpha

    mock_aiosmtplib_send.reset_mock()

    camp_b = await ph_repo.create(
        db_session,
        organization_id=ctx["org_b_id"],
        name="SMTP org B",
        template="hr_policy",
        target_dept="All",
    )
    await db_session.commit()
    await send_campaign(camp_b.id, ctx["org_b_id"], destination_url="https://safe.example/b")

    hosts_beta = {call.kwargs.get("hostname") for call in mock_aiosmtplib_send.await_args_list}
    assert "smtp.beta.test" in hosts_beta


@pytest.mark.asyncio
async def test_send_email_raises_when_smtp_missing_and_mock_disabled(monkeypatch):
    from core.mailer import send_email

    monkeypatch.setenv("SMTP_MOCK_MODE", "false")
    monkeypatch.setenv("SMTP_HOST", "")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="SMTP_HOST"):
            await send_email(
                to_email="r@example.com",
                subject="x",
                html="<p>x</p>",
                text="x",
                smtp_config=None,
            )
    finally:
        get_settings.cache_clear()
