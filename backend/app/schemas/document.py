import uuid

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    bidder_id: uuid.UUID
    document_type: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    storage_path: str | None = None
    mime_type: str | None = None
    status: str = "uploaded"


class DocumentRead(BaseModel):
    id: uuid.UUID
    bidder_id: uuid.UUID
    document_type: str
    file_name: str
    storage_path: str | None = None
    mime_type: str | None = None
    status: str
