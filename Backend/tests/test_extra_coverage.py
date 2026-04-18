"""Additional API and branch coverage toward higher overall coverage."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(client: AsyncClient, two_orgs_with_users: dict):
    ctx = two_orgs_with_users
    r = await client.post(
        "/api/auth/login",
        json={"email": ctx["admin_a_email"], "password": "WrongPassword!", "organizationId": str(ctx["org_a_id"])},
    )
    assert r.status_code == 200
    assert r.json().get("success") is False


@pytest.mark.asyncio
async def test_phishing_templates_list(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.get("/api/phishing/templates", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    t = r.json().get("templates", [])
    assert "outlook_login" in t
    assert "google_security_alert" in t
    assert "hr_policy" in t


@pytest.mark.asyncio
async def test_invalid_click_token_returns_404(client: AsyncClient):
    r = await client.get("/api/phishing/track/this-token-does-not-exist", follow_redirects=False)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_invalid_credential_token_returns_404(client: AsyncClient):
    r = await client.post(
        "/api/phishing/track/this-token-does-not-exist/credential",
        data={"username": "a@example.com", "password": "x"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_can_create_second_user(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Extra User",
            "email": "extra.user@example.com",
            "role": "trainee",
            "department": "Legal",
            "password": "ChangeMe123!",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "extra.user@example.com"


@pytest.mark.asyncio
async def test_trainee_can_list_courses(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    token = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.get("/api/courses", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_global_smtp_roundtrip(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    from modules.settings.schemas import SmtpConfig

    ctx = two_orgs_with_users
    token = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    payload = {
        "host": "smtp.global.example.com",
        "port": 587,
        "encryption": "TLS",
        "username": "",
        "password": "",
        "fromName": "CyberAware",
        "fromEmail": "noreply@example.com",
    }
    r_save = await client.post(
        "/api/settings/smtp",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r_save.status_code == 200
    r_get = await client.get("/api/settings/smtp", headers={"Authorization": f"Bearer {token}"})
    assert r_get.status_code == 200
    assert r_get.json().get("host") == "smtp.global.example.com"


@pytest.mark.asyncio
async def test_mailer_uses_mock_mode_without_aiosmtplib(monkeypatch):
    from config import get_settings
    from core.mailer import send_email

    monkeypatch.setenv("SMTP_MOCK_MODE", "true")
    get_settings.cache_clear()
    try:
        await send_email(
            to_email="recv@example.com",
            subject="Subject",
            html="<p>h</p>",
            text="t",
            smtp_config=None,
        )
    finally:
        monkeypatch.delenv("SMTP_MOCK_MODE", raising=False)
        monkeypatch.setenv("SMTP_MOCK_MODE", "false")
        get_settings.cache_clear()
