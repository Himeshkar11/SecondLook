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
    ocr_status: str | None = None
    ocr_text: str | None = None
    ocr_error: str | None = None
    ocr_completed_at: str | None = None
    ai_status: str | None = None
    ai_extraction: dict | None = None
    ai_error: str | None = None
    ai_completed_at: str | None = None
    ai_model: str | None = None
    ai_prompt_version: str | None = None
