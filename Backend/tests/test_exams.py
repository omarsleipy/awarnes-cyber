"""Exams, certificates, and LMS integration."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.security import hash_password
from modules.courses.models import Course
from modules.exams.models import Certificate, Exam, ExamPassword, ExamSession


@pytest.mark.asyncio
async def test_exam_pass_issues_certificate_when_enabled(
    client: AsyncClient,
    two_orgs_with_users: dict,
    login_helper,
    mock_aiosmtplib_send,
):
    ctx = two_orgs_with_users
    admin_tok = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    body = {
        "title": "Cert Exam",
        "certificateEnabled": True,
        "questions": [
            {"question": "Q1", "options": ["a", "b"], "correct": 0},
            {"question": "Q2", "options": ["a", "b"], "correct": 1},
        ],
        "allowed_users": [str(ctx["admin_a_user_id"])],
        "allowed_departments": [],
    }
    r = await client.post("/api/exams", json=body, headers={"Authorization": f"Bearer {admin_tok}"})
    assert r.status_code == 200
    exam_id = int(r.json()["examId"])

    pw = next(p["password"] for p in r.json()["passwords"] if p["userId"] == str(ctx["admin_a_user_id"]))

    r = await client.post(
        f"/api/exams/{exam_id}/validate-password",
        json={"password": pw},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r.json().get("valid") is True

    rq = await client.get(f"/api/exams/{exam_id}/questions", headers={"Authorization": f"Bearer {admin_tok}"})
    qs = rq.json()
    correct_indices = [0, 1]
    answers = {qs[i]["id"]: correct_indices[i] for i in range(len(qs))}

    sub = await client.post(
        f"/api/exams/{exam_id}/submit",
        json={"answers": answers},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert sub.status_code == 200
    assert sub.json()["passed"] is True

    certs = await client.get("/api/exams/certificates/me", headers={"Authorization": f"Bearer {admin_tok}"})
    assert certs.status_code == 200
    titles = [c["examTitle"] for c in certs.json()]
    assert "Cert Exam" in titles


@pytest.mark.asyncio
async def test_exam_pass_skips_certificate_when_disabled(
    client: AsyncClient,
    two_orgs_with_users: dict,
    login_helper,
    mock_aiosmtplib_send,
    db_session,
):
    ctx = two_orgs_with_users
    admin_tok = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    body = {
        "title": "No Cert Exam",
        "certificateEnabled": False,
        "questions": [{"question": "Only", "options": ["a", "b"], "correct": 0}],
        "allowed_users": [str(ctx["admin_a_user_id"])],
        "allowed_departments": [],
    }
    r = await client.post("/api/exams", json=body, headers={"Authorization": f"Bearer {admin_tok}"})
    assert r.status_code == 200
    exam_id = int(r.json()["examId"])
    pw = next(p["password"] for p in r.json()["passwords"])
    await client.post(
        f"/api/exams/{exam_id}/validate-password",
        json={"password": pw},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    rq = await client.get(f"/api/exams/{exam_id}/questions", headers={"Authorization": f"Bearer {admin_tok}"})
    q0 = rq.json()[0]
    await client.post(
        f"/api/exams/{exam_id}/submit",
        json={"answers": {q0["id"]: 0}},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )

    q = await db_session.execute(select(Certificate).where(Certificate.exam_id == exam_id))
    assert q.scalars().first() is None


@pytest.mark.asyncio
async def test_course_completion_issues_certificate_when_optional_on(
    client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session
):
    ctx = two_orgs_with_users
    db_session.add(
        Course(
            id="lms-cert-yes",
            organization_id=ctx["org_a_id"],
            title="Completion Course",
            modules=1,
            duration="10m",
            total_slides=2,
            category="Test",
            content_type="hybrid",
            content_units=[
                {"type": "text", "body": "Hello"},
                {"type": "video", "url": "https://example.com/v.mp4"},
            ],
            mid_quizzes=[
                {
                    "id": "mq1",
                    "afterUnitIndex": 0,
                    "enabled": True,
                    "questions": [{"id": "q1", "prompt": "Ready?", "options": ["yes", "no"], "correctIndex": 0}],
                }
            ],
            certificate_enabled=True,
            certificate_template_key="brand_a",
        )
    )
    await db_session.commit()

    tok = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])
    await client.patch(
        "/api/courses/lms-cert-yes/progress",
        json={"viewedSlides": 1, "quizResponses": {"mq1": {"q1": 0}}},
        headers={"Authorization": f"Bearer {tok}"},
    )
    r = await client.patch(
        "/api/courses/lms-cert-yes/progress",
        json={"viewedSlides": 2},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200

    certs = await client.get("/api/exams/certificates/me", headers={"Authorization": f"Bearer {tok}"})
    rows = certs.json()
    match = [c for c in rows if c.get("kind") == "course" and c.get("courseId") == "lms-cert-yes"]
    assert match
    assert match[0]["templateKey"] == "brand_a"


@pytest.mark.asyncio
async def test_course_no_certificate_when_optional_off(
    client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session
):
    ctx = two_orgs_with_users
    db_session.add(
        Course(
            id="lms-cert-no",
            organization_id=ctx["org_a_id"],
            title="No Certificate Course",
            modules=1,
            duration="10m",
            total_slides=1,
            category="Test",
            content_type="text",
            content_units=[{"type": "text", "body": "Only"}],
            certificate_enabled=False,
        )
    )
    await db_session.commit()

    tok = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])
    await client.patch(
        "/api/courses/lms-cert-no/progress",
        json={"viewedSlides": 1},
        headers={"Authorization": f"Bearer {tok}"},
    )

    certs = await client.get("/api/exams/certificates/me", headers={"Authorization": f"Bearer {tok}"})
    for c in certs.json():
        assert not (c.get("courseId") == "lms-cert-no")


@pytest.mark.asyncio
async def test_student_progresses_content_types_and_mid_quiz_recorded(
    client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session
):
    ctx = two_orgs_with_users
    db_session.add(
        Course(
            id="lms-flow",
            organization_id=ctx["org_a_id"],
            title="Multi Content",
            modules=1,
            duration="15m",
            total_slides=3,
            category="Test",
            content_type="hybrid",
            content_units=[
                {"type": "text", "body": "Read me"},
                {"type": "video", "url": "https://example.com/x"},
                {"type": "image", "url": "https://example.com/y.png", "caption": "Fig 1"},
            ],
            mid_quizzes=[
                {
                    "id": "mqz",
                    "afterUnitIndex": 1,
                    "enabled": True,
                    "questions": [{"id": "qq", "prompt": "2+2?", "options": ["3", "4"], "correctIndex": 1}],
                },
                {"id": "skip_quiz", "afterUnitIndex": 0, "enabled": False, "questions": []},
            ],
        )
    )
    await db_session.commit()

    tok = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])
    detail = await client.get("/api/courses/lms-flow", headers={"Authorization": f"Bearer {tok}"})
    assert detail.status_code == 200
    d = detail.json()
    assert d["contentType"] == "hybrid"
    assert len(d["contentUnits"]) == 3
    assert len(d["midQuizzes"]) == 1

    await client.patch(
        "/api/courses/lms-flow/progress",
        json={"viewedSlides": 2, "quizResponses": {"mqz": {"qq": 1}}},
        headers={"Authorization": f"Bearer {tok}"},
    )
    detail2 = await client.get("/api/courses/lms-flow", headers={"Authorization": f"Bearer {tok}"})
    assert detail2.json()["quizResponses"]["mqz"]["qq"] == 1


@pytest.mark.asyncio
async def test_certificate_pdf_download(client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session):
    ctx = two_orgs_with_users
    from modules.exams.repository import certificate_create_for_course

    db_session.add(
        Course(
            id="pdf-c",
            organization_id=ctx["org_a_id"],
            title="PDF Course",
            modules=1,
            duration="1m",
            total_slides=1,
            category="Test",
            content_units=[{"type": "text", "body": "x"}],
        )
    )
    await certificate_create_for_course(
        db_session,
        user_id=ctx["admin_a_user_id"],
        course_id="pdf-c",
        course_title="PDF Course",
        score=100,
        template_key="default",
    )
    await db_session.commit()

    tok = await login_helper(ctx["admin_a_email"], ctx["password"], ctx["org_a_id"])
    certs = await client.get("/api/exams/certificates/me", headers={"Authorization": f"Bearer {tok}"})
    cid = next(c["id"] for c in certs.json() if c.get("courseId") == "pdf-c")
    pdf = await client.get(f"/api/exams/certificates/{cid}/pdf", headers={"Authorization": f"Bearer {tok}"})
    assert pdf.status_code == 200
    assert pdf.headers.get("content-type") == "application/pdf"
    assert pdf.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_exam_violation_record(client: AsyncClient, two_orgs_with_users: dict, login_helper, db_session):
    ctx = two_orgs_with_users
    exam = Exam(title="Proc", organization_id=ctx["org_a_id"])
    db_session.add(exam)
    await db_session.flush()
    db_session.add(
        ExamPassword(
            exam_id=exam.id,
            user_id=ctx["trainee_a_user_id"],
            password_hash=hash_password("ignored"),
        )
    )
    db_session.add(ExamSession(exam_id=exam.id, user_id=ctx["trainee_a_user_id"]))
    await db_session.commit()

    tok = await login_helper(ctx["trainee_a_email"], ctx["password"], ctx["org_a_id"])
    r = await client.post(
        "/api/exams/violation/record",
        json={"examId": str(exam.id), "reason": "tab"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    assert r.json()["violationCount"] >= 1
