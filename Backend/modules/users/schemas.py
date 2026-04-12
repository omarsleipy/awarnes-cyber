"""Pydantic schemas for users."""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "trainee"
    department: str = ""


class UserCreate(UserBase):
    password: str = "ChangeMe123!"


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    department: str | None = None
    status: str | None = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str
    status: str
    completedCourses: int
    lastLogin: str

    model_config = {"from_attributes": True}


class BulkUploadResult(BaseModel):
    imported: int
    skipped: int
    errors: int


class BulkUploadRequest(BaseModel):
    csvData: str
