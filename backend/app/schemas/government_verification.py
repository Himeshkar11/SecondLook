from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GovernmentVerificationRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    bidder_id: uuid.UUID
    source: str
    provider: str
    identifier: str
    status: str
    verification_result: Optional[str] = None
    government_data: Optional[Dict[str, Any]] = None
    field_results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class DocumentVerificationResponse(BaseModel):
    document_id: str
    document_type: str
    ai_status: Optional[str] = None
    verification_status: Optional[str] = None
    latest_verification: Optional[GovernmentVerificationRead] = None
    history: List[GovernmentVerificationRead] = Field(default_factory=list)
