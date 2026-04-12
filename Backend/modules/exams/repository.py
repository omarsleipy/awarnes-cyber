"""Database queries for exams."""
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.exams.models import Exam, ExamQuestion, ExamPassword, ExamSession, Certificate


# ----- Exam -----
async def exam_get_by_id(session: AsyncSession, exam_id: int) -> Exam | None:
    result = await session.execute(select(Exam).where(Exam.id == exam_id))
    return result.scalar_one_or_none()


async def exam_create(session: AsyncSession, title: str, duration_minutes: int = 30, created_by_id: int | None = None) -> Exam:
    exam = Exam(title=title, duration_minutes=duration_minutes, created_by_id=created_by_id)
    session.add(exam)
    await session.flush()
    await session.refresh(exam)
    return exam


# ----- ExamQuestion -----
async def questions_get_by_exam(session: AsyncSession, exam_id: int) -> list[ExamQuestion]:
    result = await session.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.sort_order, ExamQuestion.id)
    )
    return list(result.scalars().all())


async def questions_create_many(session: AsyncSession, exam_id: int, questions_data: list[dict]) -> None:
    for i, q in enumerate(questions_data):
        eq = ExamQuestion(
            exam_id=exam_id,
            question_text=q["question"],
            options=q["options"],
            correct_index=q["correct"],
            sort_order=i,
        )
        session.add(eq)
    await session.flush()


# ----- ExamPassword -----
async def exam_password_get(session: AsyncSession, exam_id: int, user_id: int) -> ExamPassword | None:
    result = await session.execute(
        select(ExamPassword).where(ExamPassword.exam_id == exam_id, ExamPassword.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def exam_password_validate(session: AsyncSession, exam_id: int, user_id: int, password_hash: str) -> bool:
    row = await exam_password_get(session, exam_id, user_id)
    return row is not None and row.password_hash == password_hash


async def exam_password_upsert(session: AsyncSession, exam_id: int, user_id: int, password_hash: str) -> ExamPassword:
    row = await exam_password_get(session, exam_id, user_id)
    if row:
        row.password_hash = password_hash
        await session.flush()
        await session.refresh(row)
        return row
    row = ExamPassword(exam_id=exam_id, user_id=user_id, password_hash=password_hash)
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


# ----- ExamSession (proctoring) -----
async def session_get_active(session: AsyncSession, exam_id: int, user_id: int) -> ExamSession | None:
    result = await session.execute(
        select(ExamSession)
        .where(
            ExamSession.exam_id == exam_id,
            ExamSession.user_id == user_id,
            ExamSession.submitted_at.is_(None),
            ExamSession.disqualified.is_(False),
        )
        .order_by(ExamSession.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def session_create(session: AsyncSession, exam_id: int, user_id: int) -> ExamSession:
    s = ExamSession(exam_id=exam_id, user_id=user_id)
    session.add(s)
    await session.flush()
    await session.refresh(s)
    return s


async def session_increment_violation(session: AsyncSession, session_id: int, reason: str) -> ExamSession | None:
    result = await session.execute(select(ExamSession).where(ExamSession.id == session_id))
    s = result.scalar_one_or_none()
    if not s:
        return None
    s.violation_count += 1
    if s.violation_count >= 3:
        s.disqualified = True
        s.disqualified_reason = reason
        s.submitted_at = datetime.utcnow()
    await session.flush()
    await session.refresh(s)
    return s


async def session_submit(session: AsyncSession, session_id: int, score: int, passed: bool, answers: dict) -> None:
    result = await session.execute(select(ExamSession).where(ExamSession.id == session_id))
    s = result.scalar_one_or_none()
    if s:
        s.score = score
        s.passed = passed
        s.answers = answers
        s.submitted_at = datetime.utcnow()
        await session.flush()


async def session_get_by_id(session: AsyncSession, session_id: int) -> ExamSession | None:
    result = await session.execute(select(ExamSession).where(ExamSession.id == session_id))
    return result.scalar_one_or_none()


# ----- Certificate -----
async def certificate_create(session: AsyncSession, user_id: int, exam_id: int, exam_title: str, score: int) -> Certificate:
    expires_at = datetime.utcnow() + timedelta(days=365)
    cert = Certificate(user_id=user_id, exam_id=exam_id, exam_title=exam_title, score=score, expires_at=expires_at)
    session.add(cert)
    await session.flush()
    await session.refresh(cert)
    return cert


async def certificates_get_by_user(session: AsyncSession, user_id: int) -> list[Certificate]:
    result = await session.execute(select(Certificate).where(Certificate.user_id == user_id).order_by(Certificate.issued_at.desc()))
    return list(result.scalars().all())
