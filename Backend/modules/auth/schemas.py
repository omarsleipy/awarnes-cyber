"""Pydantic schemas for auth."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    organizationId: str | None = None


class LoginSuccessUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str
    status: str
    completedCourses: int
    lastLogin: str


class LoginSuccessResponse(BaseModel):
    success: bool = True
    user: LoginSuccessUser
    token: str


class LoginErrorResponse(BaseModel):
    success: bool = False
    error: str
