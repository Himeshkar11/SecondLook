import uuid

from pydantic import BaseModel, Field


class BidderCreate(BaseModel):
    user_id: uuid.UUID
    legal_name: str = Field(..., min_length=1)
    registration_number: str | None = None
    gst_number: str | None = None
    pan_number: str | None = None
    status: str = "pending"


class BidderRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    legal_name: str
    registration_number: str | None = None
    gst_number: str | None = None
    pan_number: str | None = None
    status: str


class BidderProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    legal_name: str
    registration_number: str | None = None
    gst_number: str | None = None
    pan_number: str | None = None
    status: str
    email: str
    full_name: str
    role: str
    active_tenders_count: int = 0
    submitted_bids_count: int = 0
    documents_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None
