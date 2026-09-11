import uuid

from pydantic import BaseModel, Field


class TenderCreate(BaseModel):
    title: str = Field(..., min_length=1)
    reference_number: str = Field(..., min_length=1)
    description: str | None = None
    status: str = "draft"
    created_by: uuid.UUID


class TenderRead(BaseModel):
    id: uuid.UUID
    title: str
    reference_number: str
    description: str | None = None
    status: str
    created_by: uuid.UUID
