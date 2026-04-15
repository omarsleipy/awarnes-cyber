"""Exam routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_organization_id, get_current_user_id, require_admin
from modules.exams.schemas import (
    ExamCreateRequest,
    GeneratePasswordsRequest,
    ReportDisqualificationRequest,
    SubmitExamRequest,
    ValidatePasswordRequest,
    ViolationRecordRequest,
)
from modules.exams import service as exam_service

router = APIRouter()


@router.post("")
async def create_exam(
    body: ExamCreateRequest,
    user_id: int = Depends(require_admin),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    res = await exam_service.create_exam(session, body, created_by_id=user_id, organization_id=organization_id)
    return {"examId": res.examId, "passwords": [p.model_dump() for p in res.passwords]}


@router.post("/{exam_id}/validate-password")
async def validate_password(
    exam_id: str,
    body: ValidatePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        eid = int(exam_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exam not found") from None
    r = await exam_service.validate_exam_password(session, eid, user_id, body.password, organization_id=organization_id)
    if not r.valid:
        return {"valid": False, "error": r.error or "Invalid exam password"}
    await exam_service.get_or_create_session(session, eid, user_id, organization_id=organization_id)
    return {"valid": True}


@router.get("/{exam_id}/questions")
async def get_questions(
    exam_id: str,
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        eid = int(exam_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exam not found") from None
    rows = await exam_service.get_exam_questions(session, eid, organization_id=organization_id)
    return [q.model_dump() for q in rows]


@router.post("/{exam_id}/submit")
async def submit(
    exam_id: str,
    body: SubmitExamRequest,
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        eid = int(exam_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exam not found") from None
    result = await exam_service.submit_exam(session, eid, user_id, body.answers, organization_id=organization_id)
    if not result:
        raise HTTPException(status_code=400, detail="No active exam session")
    return {
        "score": result.score,
        "passed": result.passed,
        "totalQuestions": result.totalQuestions,
        "correctAnswers": result.correctAnswers,
    }


@router.post("/{exam_id}/report-disqualification")
async def report_disqualification(
    exam_id: str,
    body: ReportDisqualificationRequest,
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        eid = int(exam_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exam not found") from None
    await exam_service.report_disqualification(session, eid, user_id, body.reason, organization_id=organization_id)
    return {"success": True}


@router.get("/certificates/me")
async def my_certificates(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    rows = await exam_service.get_certificates_for_user(session, user_id)
    return [c.model_dump() for c in rows]


@router.get("/certificates/{certificate_id}/pdf")
async def certificate_pdf(
    certificate_id: str,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        cid = int(certificate_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Certificate not found") from None
    pdf_bytes = await exam_service.generate_certificate_pdf(session, cid, user_id)
    if pdf_bytes is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="certificate-{cid}.pdf"'},
    )


@router.post("/violation/record")
async def violation_record(
    body: ViolationRecordRequest,
    user_id: int = Depends(get_current_user_id),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        exam_id = int(body.examId)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exam not found") from None
    disqualified, count = await exam_service.record_violation(
        session,
        exam_id=exam_id,
        user_id=user_id,
        reason=body.reason,
        organization_id=organization_id,
    )
    return {"success": True, "violationCount": count, "disqualified": disqualified}


@router.post("/{exam_id}/generate-passwords")
async def generate_passwords(
    exam_id: str,
    body: GeneratePasswordsRequest,
    user_id: int = Depends(require_admin),
    organization_id: int = Depends(get_current_organization_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        eid = int(exam_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exam not found") from None
    res = await exam_service.generate_exam_passwords(session, eid, body.userIds, organization_id=organization_id)
    return {"passwords": [p.model_dump() for p in res.passwords]}
