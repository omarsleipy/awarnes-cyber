"""Exam business logic: create exam, validate password, questions, submit, proctoring."""
import secrets
import string
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

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
from modules.users.repository import get_by_id as user_get_by_id


def _generate_exam_password(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def create_exam(session: AsyncSession, payload: ExamCreateRequest, created_by_id: int | None) -> ExamCreateResponse:
    exam = await repo.exam_create(session, title=payload.title)
    questions_data = [
        {"question": q.question, "options": q.options, "correct": q.correct}
        for q in payload.questions
    ]
    await repo.questions_create_many(session, exam.id, questions_data)
    passwords_out: list[ExamPasswordEntry] = []
    for uid in payload.allowed_users:
        try:
            user_id = int(uid)
        except (ValueError, TypeError):
            continue
        user = await user_get_by_id(session, user_id)
        if not user:
            continue
        plain = _generate_exam_password()
        hashed = hash_password(plain)
        await repo.exam_password_upsert(session, exam.id, user_id, hashed)
        passwords_out.append(ExamPasswordEntry(userId=str(user_id), password=plain))
    return ExamCreateResponse(examId=str(exam.id), passwords=passwords_out)


async def validate_exam_password(session: AsyncSession, exam_id: int, user_id: int, password: str) -> ValidatePasswordResponse:
    exam = await repo.exam_get_by_id(session, exam_id)
    if not exam:
        return ValidatePasswordResponse(valid=False, error="Exam not found")
    row = await repo.exam_password_get(session, exam_id, user_id)
    if not row:
        return ValidatePasswordResponse(valid=False, error="Invalid exam password")
    if not verify_password(password, row.password_hash):
        return ValidatePasswordResponse(valid=False, error="Invalid exam password")
    return ValidatePasswordResponse(valid=True)


async def get_exam_questions(session: AsyncSession, exam_id: int) -> list[ExamQuestionPublic]:
    exam = await repo.exam_get_by_id(session, exam_id)
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


async def get_or_create_session(session: AsyncSession, exam_id: int, user_id: int) -> int | None:
    """Returns session id if exam exists and user has access (password already validated)."""
    exam = await repo.exam_get_by_id(session, exam_id)
    if not exam:
        return None
    active = await repo.session_get_active(session, exam_id, user_id)
    if active:
        return active.id
    s = await repo.session_create(session, exam_id, user_id)
    return s.id


async def record_violation(session: AsyncSession, exam_id: int, user_id: int, reason: str) -> tuple[bool, int]:
    """Record proctoring violation. Returns (disqualified, new_violation_count)."""
    active = await repo.session_get_active(session, exam_id, user_id)
    if not active:
        return False, 0
    updated = await repo.session_increment_violation(session, active.id, reason)
    if not updated:
        return False, 0
    return updated.disqualified, updated.violation_count


async def submit_exam(session: AsyncSession, exam_id: int, user_id: int, answers: dict[str, int]) -> SubmitExamResponse | None:
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
    if passed:
        exam = await repo.exam_get_by_id(session, exam_id)
        await repo.certificate_create(session, user_id, exam_id, exam.title if exam else "Exam", score)
    return SubmitExamResponse(score=score, passed=passed, totalQuestions=total, correctAnswers=correct)


async def report_disqualification(session: AsyncSession, exam_id: int, user_id: int, reason: str) -> bool:
    """Mark session disqualified (e.g. after 3rd violation from frontend)."""
    active = await repo.session_get_active(session, exam_id, user_id)
    if not active:
        return False
    active.disqualified = True
    active.disqualified_reason = reason
    active.submitted_at = datetime.utcnow()
    await session.flush()
    return True


async def generate_exam_passwords(session: AsyncSession, exam_id: int, user_ids: list[str]) -> GeneratePasswordsResponse:
    exam = await repo.exam_get_by_id(session, exam_id)
    if not exam:
        return GeneratePasswordsResponse(passwords=[])
    passwords_out: list[ExamPasswordEntry] = []
    for uid in user_ids:
        try:
            user_id = int(uid)
        except (ValueError, TypeError):
            continue
        user = await user_get_by_id(session, user_id)
        if not user:
            continue
        plain = _generate_exam_password()
        hashed = hash_password(plain)
        await repo.exam_password_upsert(session, exam_id, user_id, hashed)
        passwords_out.append(ExamPasswordEntry(userId=str(user_id), password=plain))
    return GeneratePasswordsResponse(passwords=passwords_out)


async def get_certificates_for_user(session: AsyncSession, user_id: int) -> list[CertificateResponse]:
    certs = await repo.certificates_get_by_user(session, user_id)
    return [
        CertificateResponse(
            id=str(c.id),
            examTitle=c.exam_title,
            score=c.score,
            date=c.issued_at.strftime("%Y-%m-%d"),
            status=c.status,
            expiresAt=c.expires_at.strftime("%Y-%m-%d"),
        )
        for c in certs
    ]
