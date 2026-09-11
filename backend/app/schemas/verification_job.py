import uuid

from pydantic import BaseModel, Field


class VerificationJobCreate(BaseModel):
    bidder_id: uuid.UUID
    document_id: uuid.UUID | None = None
    verification_type: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    status: str = "pending"


class VerificationJobRead(BaseModel):
    id: uuid.UUID
    bidder_id: uuid.UUID
    document_id: uuid.UUID | None = None
    verification_type: str
    provider: str
    status: str
