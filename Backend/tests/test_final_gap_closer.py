"""Targeted coverage: exams/service, auth/service edges, LMS certificate E2E."""

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from core.security import hash_password
from modules.auth import service as auth_service
from modules.courses.models import Course
from modules.exams import service as exam_service
from modules.exams.models import Exam, ExamPassword, ExamSession
from modules.exams.schemas import ExamCreateRequest, QuestionOption
from modules.organizations.models import Organization
from modules.users.models import User


@pytest.mark.asyncio
async def test_record_violation_disqualifies_on_third_strike(db_session, two_orgs_with_users):
    ctx = two_orgs_with_users
    exam = Exam(title="Violation Exam", organization_id=ctx["org_a_id"])
    db_session.add(exam)
    await db_session.flush()
    db_session.add(
        ExamPassword(
            exam_id=exam.id,
            user_id=ctx["trainee_a_user_id"],
            password_hash=hash_password("temp"),
        )
    )
    db_session.add(
        ExamSession(exam_id=exam.id, user_id=ctx["trainee_a_user_id"])
    )
    await db_session.commit()

    d1, c1 = await exam_service.record_violation(
        db_session,
        exam.id,
        ctx["trainee_a_user_id"],
        "blur",
        ctx["org_a_id"],
    )
    await db_session.commit()
    assert d1 is False and c1 == 1

    d2, c2 = await exam_service.record_violation(
        db_session,
        exam.id,
        ctx["trainee_a_user_id"],
        "blur",
        ctx["org_a_id"],
    )
    await db_session.commit()
    assert d2 is False and c2 == 2

    d3, c3 = await exam_service.record_violation(
        db_session,
        exam.id,
        ctx["trainee_a_user_id"],
        "blur",
        ctx["org_a_id"],
    )
    await db_session.commit()
    assert d3 is True and c3 == 3


@pytest.mark.asyncio
async def test_record_violation_returns_false_without_active_session(db_session, two_orgs_with_users):
    ctx = two_orgs_with_users
    exam = Exam(title="No Session Violation", organization_id=ctx["org_a_id"])
    db_session.add(exam)
    await db_session.commit()

    dq, cnt = await exam_service.record_violation(
        db_session,
        exam.id,
        ctx["trainee_a_user_id"],
        "x",
        ctx["org_a_id"],
    )
    assert dq is False and cnt == 0


@pytest.mark.asyncio
async def test_generate_exam_passwords_returns_empty_for_unknown_exam(db_session, two_orgs_with_users):
    ctx = two_orgs_with_users
    res = await exam_service.generate_exam_passwords(
        db_session,
        exam_id=999_999_999,
        user_ids=[str(ctx["admin_a_user_id"])],
        organization_id=ctx["org_a_id"],
    )
    assert res.passwords == []


@pytest.mark.asyncio
async def test_generate_exam_passwords_returns_entries(
    db_session, two_orgs_with_users, mock_aiosmtplib_send
):
    ctx = two_orgs_with_users
    exam = Exam(title="Pwd Gen", organization_id=ctx["org_a_id"])
    db_session.add(exam)
    await db_session.commit()

    res = await exam_service.generate_exam_passwords(
        db_session,
        exam_id=exam.id,
        user_ids=[str(ctx["trainee_a_user_id"])],
        organization_id=ctx["org_a_id"],
    )
    assert len(res.passwords) == 1
    assert res.passwords[0].userId == str(ctx["trainee_a_user_id"])


@pytest.mark.asyncio
async def test_create_exam_survives_smtp_failure(monkeypatch, db_session, two_orgs_with_users):
    ctx = two_orgs_with_users

    async def send_fail(**_kwargs):
        raise ConnectionError("SMTP unavailable")

    monkeypatch.setattr("modules.exams.service.send_email", send_fail)

    payload = ExamCreateRequest(
        title="Resilient Exam",
        questions=[QuestionOption(question="Q1", options=["a", "b"], correct=0)],
        allowed_users=[str(ctx["admin_a_user_id"])],
        allowed_departments=[],
        certificateEnabled=True,
    )
    out = await exam_service.create_exam(
        db_session,
        payload,
        created_by_id=ctx["admin_a_user_id"],
        organization_id=ctx["org_a_id"],
    )
    await db_session.commit()

    assert out.examId
    assert len(out.passwords) == 1
    assert out.passwords[0].userId == str(ctx["admin_a_user_id"])


@pytest.mark.asyncio
async def test_login_rejects_suspended_organization(client: AsyncClient, two_orgs_with_users: dict, db_session):
    ctx = two_orgs_with_users
    await db_session.execute(
        update(Organization).where(Organization.id == ctx["org_a_id"]).values(status="suspended")
    )
    await db_session.commit()

    r = await client.post(
        "/api/auth/login",
        json={
            "email": ctx["admin_a_email"],
            "password": ctx["password"],
            "organizationId": str(ctx["org_a_id"]),
        },
    )
    body = r.json()
    assert body.get("success") is False
    assert "suspended" in (body.get("error") or "").lower()


@pytest.mark.asyncio
async def test_auth_service_duplicate_email_requires_organization_id(db_session):
    o1 = Organization(name="Dup Org One", status="active", auth_mode="local")
    o2 = Organization(name="Dup Org Two", status="active", auth_mode="local")
    db_session.add_all([o1, o2])
    await db_session.flush()
    pw = hash_password("SharedPwd123!")
    db_session.add_all(
        [
            User(
                organization_id=o1.id,
                email="shared@example.com",
                name="U1",
                role="trainee",
                hashed_password=pw,
            ),
            User(
                organization_id=o2.id,
                email="shared@example.com",
                name="U2",
                role="trainee",
                hashed_password=pw,
            ),
        ]
    )
    await db_session.commit()

    out = await auth_service.login(db_session, "shared@example.com", "SharedPwd123!", organization_id=None)
    assert out["success"] is False
    assert "organization" in (out.get("error") or "").lower()

    ok = await auth_service.login(db_session, "shared@example.com", "SharedPwd123!", organization_id=str(o2.id))
    assert ok["success"] is True
    assert ok["user"]["name"] == "U2"


@pytest.mark.asyncio
async def test_hybrid_course_to_pdf_certificate_end_to_end(
    client: AsyncClient,
    two_orgs_with_users: dict,
    login_helper,
    db_session,
):
    ctx = two_orgs_with_users
    db_session.add(
        Course(
            id="lms-e2e-hybrid",
            organization_id=ctx["org_a_id"],
            title="Hybrid E2E Course",
            modules=2,
            duration="20m",
            category="Training",
            content_type="hybrid",
            content_units=[
                {"type": "text", "body": "Chapter 1"},
                {"type": "video", "url": "https://example.com/lesson.mp4"},
            ],
            mid_quizzes=[
                {
                    "id": "mid1",
                    "afterUnitIndex": 0,
                    "enabled": True,
                    "questions": [{"id": "qq1", "prompt": "Ack?", "options": ["ok", "no"], "correctIndex": 0}],
                }
            ],
            certificate_enabled=True,
            certificate_template_key="default",
        )
    )
    await db_session.commit()

    tok = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])

    dash = await client.get("/api/courses", headers={"Authorization": f"Bearer {tok}"})
    assert any(c["id"] == "lms-e2e-hybrid" for c in dash.json())

    detail = await client.get("/api/courses/lms-e2e-hybrid", headers={"Authorization": f"Bearer {tok}"})
    assert detail.status_code == 200
    assert detail.json()["contentType"] == "hybrid"
    assert len(detail.json()["contentUnits"]) == 2

    await client.patch(
        "/api/courses/lms-e2e-hybrid/progress",
        json={"viewedSlides": 1, "quizResponses": {"mid1": {"qq1": 0}}},
        headers={"Authorization": f"Bearer {tok}"},
    )
    fin = await client.patch(
        "/api/courses/lms-e2e-hybrid/progress",
        json={"viewedSlides": 2},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert fin.status_code == 200

    certs = await client.get("/api/exams/certificates/me", headers={"Authorization": f"Bearer {tok}"})
    assert certs.status_code == 200
    row = next(
        (c for c in certs.json() if c.get("kind") == "course" and c.get("courseId") == "lms-e2e-hybrid"),
        None,
    )
    assert row is not None
    assert row["examTitle"] == "Hybrid E2E Course"

    pdf = await client.get(
        f"/api/exams/certificates/{row['id']}/pdf",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert pdf.status_code == 200
    assert pdf.headers.get("content-type") == "application/pdf"
    assert pdf.content[:4] == b"%PDF"
