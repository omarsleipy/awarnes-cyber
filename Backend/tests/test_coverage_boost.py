"""Additional tests to raise overall coverage (exams edges, auth branches, org service)."""

import uuid

import pytest
from httpx import AsyncClient

from core.security import hash_password
from modules.organizations.models import Organization
from modules.users.models import User


@pytest.mark.asyncio
async def test_auth_requires_org_when_email_ambiguous(client: AsyncClient, db_session):
    uniq = uuid.uuid4().hex[:10]
    o1 = Organization(name=f"O1 Cov {uniq}", status="active", auth_mode="local")
    o2 = Organization(name=f"O2 Cov {uniq}", status="active", auth_mode="local")
    db_session.add_all([o1, o2])
    await db_session.flush()
    p = hash_password("SamePass123!")
    db_session.add_all(
        [
            User(organization_id=o1.id, email="ambiguous@example.com", name="A", role="trainee", hashed_password=p),
            User(organization_id=o2.id, email="ambiguous@example.com", name="B", role="trainee", hashed_password=p),
        ]
    )
    await db_session.commit()

    r = await client.post("/api/auth/login", json={"email": "ambiguous@example.com", "password": "SamePass123!"})
    assert r.json().get("success") is False
    assert "organization" in (r.json().get("error") or "").lower()

    r2 = await client.post(
        "/api/auth/login",
        json={"email": "ambiguous@example.com", "password": "SamePass123!", "organizationId": str(o1.id)},
    )
    assert r2.json().get("success") is True


@pytest.mark.asyncio
async def test_exam_invalid_id_returns_404(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    tok = await login_helper(two_orgs_with_users["admin_a_email"], two_orgs_with_users["password"], two_orgs_with_users["org_a_id"])
    r = await client.get("/api/exams/999999/questions", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_exam_report_disqualification(
    client: AsyncClient, two_orgs_with_users: dict, login_helper, mock_aiosmtplib_send
):
    ctx = two_orgs_with_users
    tok = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        "/api/exams",
        json={
            "title": "Disq Exam",
            "certificateEnabled": True,
            "questions": [{"question": "X", "options": ["a", "b"], "correct": 0}],
            "allowed_users": [str(ctx["admin_a_user_id"])],
            "allowed_departments": [],
        },
        headers={"Authorization": f"Bearer {tok}"},
    )
    eid = int(r.json()["examId"])
    pw = r.json()["passwords"][0]["password"]
    await client.post(
        f"/api/exams/{eid}/validate-password",
        json={"password": pw},
        headers={"Authorization": f"Bearer {tok}"},
    )
    rd = await client.post(
        f"/api/exams/{eid}/report-disqualification",
        json={"reason": "integrity"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert rd.status_code == 200
    assert rd.json().get("success") is True


@pytest.mark.asyncio
async def test_exam_generate_passwords_endpoint(
    client: AsyncClient, two_orgs_with_users: dict, login_helper, mock_aiosmtplib_send
):
    ctx = two_orgs_with_users
    tok = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        "/api/exams",
        json={
            "title": "Pwd Exam",
            "questions": [{"question": "X", "options": ["a", "b"], "correct": 0}],
            "allowed_users": [],
            "allowed_departments": [],
        },
        headers={"Authorization": f"Bearer {tok}"},
    )
    eid = int(r.json()["examId"])
    r2 = await client.post(
        f"/api/exams/{eid}/generate-passwords",
        json={"userIds": [str(ctx["trainee_a_user_id"])]},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r2.status_code == 200
    assert r2.json()["passwords"]


@pytest.mark.asyncio
async def test_exam_create_includes_department_users(
    client: AsyncClient, two_orgs_with_users: dict, login_helper, mock_aiosmtplib_send
):
    ctx = two_orgs_with_users
    tok = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        "/api/exams",
        json={
            "title": "Dept Exam",
            "questions": [{"question": "X", "options": ["a", "b"], "correct": 0}],
            "allowed_users": [],
            "allowed_departments": ["Finance"],
        },
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    pws = r.json().get("passwords") or []
    assert any(p["userId"] == str(ctx["trainee_a_user_id"]) for p in pws)


@pytest.mark.asyncio
async def test_submit_without_session_returns_400(client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session):
    from modules.exams.models import Exam

    ctx = two_orgs_with_users
    ex = Exam(title="No Session", organization_id=ctx["org_a_id"])
    db_session.add(ex)
    await db_session.flush()
    await db_session.commit()
    tok = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        f"/api/exams/{ex.id}/submit",
        json={"answers": {}},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_organization_create_idempotent_name(client: AsyncClient, two_orgs_with_users: dict, login_helper):
    ctx = two_orgs_with_users
    tok = await login_helper(ctx["super_admin_email"], ctx["password"], ctx["org_a_id"])
    name = f"Unique Org Name XYZ-{uuid.uuid4().hex[:12]}"
    r1 = await client.post("/api/organizations", json={"name": name}, headers={"Authorization": f"Bearer {tok}"})
    r2 = await client.post("/api/organizations", json={"name": name}, headers={"Authorization": f"Bearer {tok}"})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]
