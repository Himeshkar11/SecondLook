import uuid

from pydantic import BaseModel, Field


class VerificationResultRead(BaseModel):
    id: uuid.UUID
    verification_job_id: uuid.UUID
    status: str = Field(..., min_length=1)
    result: dict | None = None
    confidence: float | None = None
    message: str | None = None
