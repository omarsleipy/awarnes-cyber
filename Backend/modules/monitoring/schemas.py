"""Pydantic schemas for monitoring."""
from pydantic import BaseModel


class ActivityCreate(BaseModel):
    activity_type: str
    severity: str = "warning"
    title: str
    details: str | None = None
    exam_id: int | None = None


class ActivityResponse(BaseModel):
    id: str
    organization_id: str | None = None
    user_id: str | None
    activity_type: str
    severity: str
    title: str
    details: str | None
    ip_address: str | None
    exam_id: int | None
    phishing_campaign_id: str | None = None
    phishing_recipient_id: str | None = None
    created_at: str

    model_config = {"from_attributes": True}
