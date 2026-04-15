from pydantic import BaseModel


class CampaignOut(BaseModel):
    id: str
    name: str
    template: str
    targetDept: str
    sent: int
    clicked: int
    reported: int
    status: str
    createdAt: str

    model_config = {"from_attributes": False}


class CampaignCreate(BaseModel):
    name: str | None = None
    template: str = ""
    targetDept: str = "All"
    destinationUrl: str = "https://example.com"


class CampaignSendRequest(BaseModel):
    destinationUrl: str | None = None
