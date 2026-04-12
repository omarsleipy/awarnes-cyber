"""Pydantic schemas for monitoring."""
from datetime import datetime
from pydantic import BaseModel


class ActivityCreate(BaseModel):
    activity_type: str
    severity: str = "warning"
    title: str
    details: str | None = None
    exam_id: int | None = None


class ActivityResponse(BaseModel):
    id: str
    user_id: str | None
    activity_type: str
    severity: str
    title: str
    details: str | None
    ip_address: str | None
    exam_id: int | None
    created_at: str

    model_config = {"from_attributes": True}
