"""Pydantic schemas for Tender Bid Workspaces and Submissions (Milestone 08)."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BidDocumentRead(BaseModel):
    """Sanitized document metadata for documents attached to a bid."""
    id: UUID
    file_name: str
    document_type: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: str
    ocr_status: Optional[str] = None
    ai_status: Optional[str] = None
    verification_status: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BidRead(BaseModel):
    """Read representation of a bidder's submission workspace for a tender."""
    id: UUID
    bidder_id: UUID
    tender_id: UUID
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tender_title: Optional[str] = None
    tender_reference_number: Optional[str] = None
    tender_organization: Optional[str] = None
    tender_status: Optional[str] = None
    tender_closing_date: Optional[datetime] = None
    documents_count: int = 0
    documents: List[BidDocumentRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BidCreateRequest(BaseModel):
    """Payload to start a bid submission workspace for a tender."""
    tender_id: UUID


class BidSubmitResponse(BaseModel):
    """Response returned upon formal bid submission."""
    id: UUID
    status: str
    submitted_at: datetime
    message: str = "Bid submitted successfully for statutory evaluation."

    model_config = ConfigDict(from_attributes=True)
