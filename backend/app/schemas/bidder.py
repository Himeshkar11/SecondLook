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
