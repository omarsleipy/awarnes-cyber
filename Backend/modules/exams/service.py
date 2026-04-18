"""Exam business logic: create exam, validate password, questions, submit, proctoring."""
import logging
import secrets
import string
from io import BytesIO
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from config import get_settings
from core.mailer import send_email
from core.security import hash_password, verify_password
from modules.exams import repository as repo
from modules.exams.schemas import (
    ExamCreateRequest,
    ExamCreateResponse,
    ExamPasswordEntry,
    ValidatePasswordResponse,
    ExamQuestionPublic,
    SubmitExamResponse,
    GeneratePasswordsResponse,
    CertificateResponse,
)
from modules.users.repository import get_by_department, get_by_id as user_get_by_id

logger = logging.getLogger(__name__)


def _generate_exam_password(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _send_exam_password_email(
    *,
    to_email: str,
    full_name: str,
    exam_id: int,
    exam_title: str,
    password: str,
) -> None:
    settings = get_settings()
    exam_link = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/exam/{exam_id}"
    subject = f"Your temporary password for {exam_title}"
    text = (
        f"Hi {full_name},\n\n"
        f"You have been assigned an exam: {exam_title}\n"
        f"Temporary password: {password}\n"
        f"Start exam: {exam_link}\n\n"
        "This password is temporary and intended only for your use."
    )
    html = (
        f"<p>Hi {full_name},</p>"
        f"<p>You have been assigned an exam: <strong>{exam_title}</strong>.</p>"
        f"<p><strong>Temporary password:</strong> {password}</p>"
        f"<p><a href='{exam_link}'>Start exam</a></p>"
        "<p>This password is temporary and intended only for your use.</p>"
    )
    await send_email(to_email=to_email, subject=subject, html=html, text=text)


async def _assign_and_notify_exam_passwords(
    *,
    session: AsyncSession,
    organization_id: int,
    exam_id: int,
    exam_title: str,
    user_ids: list[str],
) -> list[ExamPasswordEntry]:
    passwords_out: list[ExamPasswordEntry] = []
    for uid in user_ids:
        try:
            user_id = int(uid)
        except (ValueError, TypeError):
            continue
        user = await user_get_by_id(session, user_id)
        if not user or user.organization_id != organization_id:
            continue
        plain = _generate_exam_password()
        hashed = hash_password(plain)
        await repo.exam_password_upsert(session, exam_id, user_id, hashed)
        passwords_out.append(ExamPasswordEntry(userId=str(user_id), password=plain))
        try:
            await _send_exam_password_email(
                to_email=user.email,
                full_name=user.name,
                exam_id=exam_id,
                exam_title=exam_title,
                password=plain,
            )
        except Exception:
            logger.exception("Failed sending exam password email to %s for exam %s", user.email, exam_id)
    return passwords_out


async def create_exam(
    session: AsyncSession,
    payload: ExamCreateRequest,
    created_by_id: int | None,
    organization_id: int,
) -> ExamCreateResponse:
    exam = await repo.exam_create(
        session,
        title=payload.title,
        organization_id=organization_id,
        certificate_enabled=payload.certificateEnabled,
    )
    questions_data = [
        {"question": q.question, "options": q.options, "correct": q.correct}
        for q in payload.questions
    ]
    await repo.questions_create_many(session, exam.id, questions_data)
    user_ids = set(payload.allowed_users)
    for department in payload.allowed_departments:
        dep_users = await get_by_department(session, organization_id=organization_id, department=department)
        for user in dep_users:
            user_ids.add(str(user.id))
    passwords_out = await _assign_and_notify_exam_passwords(
        session=session,
        organization_id=organization_id,
        exam_id=exam.id,
        exam_title=exam.title,
        user_ids=list(user_ids),
    )
    return ExamCreateResponse(examId=str(exam.id), passwords=passwords_out)


async def validate_exam_password(
    session: AsyncSession,
    exam_id: int,
    user_id: int,
    password: str,
    organization_id: int,
) -> ValidatePasswordResponse:
    exam = await repo.exam_get_by_id(session, exam_id, organization_id=organization_id)
    if not exam:
        return ValidatePasswordResponse(valid=False, error="Exam not found")
    row = await repo.exam_password_get(session, exam_id, user_id)
    if not row:
        return ValidatePasswordResponse(valid=False, error="Invalid exam password")
    if not verify_password(password, row.password_hash):
        return ValidatePasswordResponse(valid=False, error="Invalid exam password")
    return ValidatePasswordResponse(valid=True)


async def get_exam_questions(session: AsyncSession, exam_id: int, organization_id: int) -> list[ExamQuestionPublic]:
    exam = await repo.exam_get_by_id(session, exam_id, organization_id=organization_id)
    if not exam:
        return []
    questions = await repo.questions_get_by_exam(session, exam_id)
    return [
        ExamQuestionPublic(
            id=f"q{q.id}",
            question=q.question_text,
            options=q.options,
        )
        for q in questions
    ]


async def get_or_create_session(
    session: AsyncSession,
    exam_id: int,
    user_id: int,
    organization_id: int,
) -> int | None:
    """Returns session id if exam exists and user has access (password already validated)."""
    exam = await repo.exam_get_by_id(session, exam_id, organization_id=organization_id)
    if not exam:
        return None
    active = await repo.session_get_active(session, exam_id, user_id)
    if active:
        return active.id
    s = await repo.session_create(session, exam_id, user_id)
    return s.id


async def record_violation(
    session: AsyncSession,
    exam_id: int,
    user_id: int,
    reason: str,
    organization_id: int,
) -> tuple[bool, int]:
    """Record proctoring violation. Returns (disqualified, new_violation_count)."""
    exam = await repo.exam_get_by_id(session, exam_id, organization_id=organization_id)
    if not exam:
        return False, 0
    active = await repo.session_get_active(session, exam_id, user_id)
    if not active:
        return False, 0
    updated = await repo.session_increment_violation(session, active.id, reason)
    if not updated:
        return False, 0
    return updated.disqualified, updated.violation_count


async def submit_exam(
    session: AsyncSession,
    exam_id: int,
    user_id: int,
    answers: dict[str, int],
    organization_id: int,
) -> SubmitExamResponse | None:
    exam = await repo.exam_get_by_id(session, exam_id, organization_id=organization_id)
    if not exam:
        return None
    active = await repo.session_get_active(session, exam_id, user_id)
    if not active:
        return None
    questions = await repo.questions_get_by_exam(session, exam_id)
    correct = 0
    for q in questions:
        key = f"q{q.id}"
        if answers.get(key) == q.correct_index:
            correct += 1
    total = len(questions)
    score = round((correct / total) * 100) if total else 0
    passed = score >= 70
    await repo.session_submit(session, active.id, score, passed, answers)
    if passed and getattr(exam, "certificate_enabled", True):
        await repo.certificate_create_for_exam(session, user_id, exam_id, exam.title if exam else "Exam", score)
    return SubmitExamResponse(score=score, passed=passed, totalQuestions=total, correctAnswers=correct)


async def report_disqualification(
    session: AsyncSession,
    exam_id: int,
    user_id: int,
    reason: str,
    organization_id: int,
) -> bool:
    """Mark session disqualified (e.g. after 3rd violation from frontend)."""
    exam = await repo.exam_get_by_id(session, exam_id, organization_id=organization_id)
    if not exam:
        return False
    active = await repo.session_get_active(session, exam_id, user_id)
    if not active:
        return False
    active.disqualified = True
    active.disqualified_reason = reason
    active.submitted_at = datetime.utcnow()
    await session.flush()
    return True


async def generate_exam_passwords(
    session: AsyncSession,
    exam_id: int,
    user_ids: list[str],
    organization_id: int,
) -> GeneratePasswordsResponse:
    exam = await repo.exam_get_by_id(session, exam_id, organization_id=organization_id)
    if not exam:
        return GeneratePasswordsResponse(passwords=[])
    passwords_out = await _assign_and_notify_exam_passwords(
        session=session,
        organization_id=organization_id,
        exam_id=exam_id,
        exam_title=exam.title,
        user_ids=user_ids,
    )
    return GeneratePasswordsResponse(passwords=passwords_out)


async def get_certificates_for_user(session: AsyncSession, user_id: int) -> list[CertificateResponse]:
    certs = await repo.certificates_get_by_user(session, user_id)
    out: list[CertificateResponse] = []
    for c in certs:
        kind = "course" if c.course_id else "exam"
        tk = getattr(c, "certificate_template_key", None) or "default"
        out.append(
            CertificateResponse(
                id=str(c.id),
                examTitle=c.exam_title,
                score=c.score,
                date=c.issued_at.strftime("%Y-%m-%d"),
                status=c.status,
                expiresAt=c.expires_at.strftime("%Y-%m-%d"),
                kind=kind,
                courseId=c.course_id,
                templateKey=tk,
            )
        )
    return out


async def generate_certificate_pdf(
    session: AsyncSession,
    certificate_id: int,
    user_id: int,
) -> bytes | None:
    cert = await repo.certificate_get_by_id_for_user(session, certificate_id, user_id)
    if not cert:
        return None
    user = await user_get_by_id(session, user_id)
    full_name = user.name if user else "User"

    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER

    tmpl = getattr(cert, "certificate_template_key", None) or "default"
    pdf.setFillColor(colors.HexColor("#355C7D") if tmpl == "brand_a" else colors.black)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 130, "Certificate of Completion")

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 180, "This certifies that")

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 220, full_name)

    pdf.setFont("Helvetica", 13)
    subtitle = "has successfully completed" if cert.course_id else "has successfully passed"
    pdf.drawCentredString(width / 2, height - 255, subtitle)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 290, cert.exam_title)

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 330, f"Score: {cert.score}%")
    pdf.drawCentredString(width / 2, height - 350, f"Issued: {cert.issued_at.strftime('%Y-%m-%d')}")
    pdf.drawCentredString(width / 2, height - 370, f"Expires: {cert.expires_at.strftime('%Y-%m-%d')}")

    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawCentredString(width / 2, 60, "Generated by CyberAware")

    pdf.showPage()
    pdf.save()
    return buf.getvalue()
