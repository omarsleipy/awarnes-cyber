"""Pydantic schemas for exams."""
from pydantic import BaseModel


class QuestionOption(BaseModel):
    question: str
    options: list[str]
    correct: int


class ExamCreateRequest(BaseModel):
    title: str
    questions: list[QuestionOption]
    allowed_users: list[str]  # user ids


class ExamPasswordEntry(BaseModel):
    userId: str
    password: str


class ExamCreateResponse(BaseModel):
    examId: str
    passwords: list[ExamPasswordEntry]


class ValidatePasswordRequest(BaseModel):
    password: str


class ValidatePasswordResponse(BaseModel):
    valid: bool
    error: str | None = None


class ExamQuestionOut(BaseModel):
    id: str
    question: str
    options: list[str]
    correct: int


class ExamQuestionPublic(BaseModel):
    """Sent to the client (no correct answer index)."""

    id: str
    question: str
    options: list[str]


class SubmitExamRequest(BaseModel):
    answers: dict[str, int]  # question_id -> option_index


class SubmitExamResponse(BaseModel):
    score: int
    passed: bool
    totalQuestions: int
    correctAnswers: int


class ReportDisqualificationRequest(BaseModel):
    reason: str


class GeneratePasswordsRequest(BaseModel):
    userIds: list[str]


class GeneratePasswordsResponse(BaseModel):
    passwords: list[ExamPasswordEntry]


class CertificateResponse(BaseModel):
    id: str
    examTitle: str
    score: int
    date: str
    status: str
    expiresAt: str
