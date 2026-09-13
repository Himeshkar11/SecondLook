"""Pydantic schemas for Task 16 Officer Review Layer."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums / constants
# ---------------------------------------------------------------------------

REVIEW_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED"}
OFFICER_DECISIONS = {"QUALIFIED", "NOT_QUALIFIED", "REQUIRES_CLARIFICATION", "WITHDRAWN", "NO_DECISION"}
REQUIREMENT_REVIEW_STATUSES = {"NOT_REVIEWED", "REVIEWED", "FLAGGED"}


# ---------------------------------------------------------------------------
# RequirementReview schemas
# ---------------------------------------------------------------------------


class RequirementReviewRead(BaseModel):
    id: uuid.UUID
    review_id: uuid.UUID
    requirement_result_id: uuid.UUID
    review_status: str
    officer_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}


class RequirementReviewUpdate(BaseModel):
    status: str = Field(..., description="REVIEWED or FLAGGED")
    comment: Optional[str] = Field(None, description="Officer comment for this requirement")


# ---------------------------------------------------------------------------
# OfficerReview schemas
# ---------------------------------------------------------------------------


class OfficerReviewRead(BaseModel):
    id: uuid.UUID
    evaluation_id: uuid.UUID
    reviewer_id: Optional[uuid.UUID] = None
    status: str
    decision: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    requirement_reviews: List[RequirementReviewRead] = []

    model_config = {"from_attributes": True}


class OfficerReviewCreate(BaseModel):
    reviewer_id: Optional[uuid.UUID] = Field(None, description="Reviewer user ID (optional)")
    notes: Optional[str] = None


class OfficerDecisionUpdate(BaseModel):
    decision: str = Field(..., description="QUALIFIED | NOT_QUALIFIED | REQUIRES_CLARIFICATION | WITHDRAWN | NO_DECISION")
    notes: Optional[str] = Field(None, description="Overall review notes")


# ---------------------------------------------------------------------------
# Compliance summary embedded in review payload
# ---------------------------------------------------------------------------


class ComplianceSummaryRead(BaseModel):
    total: int
    passed: int
    failed: int
    partial: int
    not_verified: int
    not_applicable: int


# ---------------------------------------------------------------------------
# Requirement result item for review display
# ---------------------------------------------------------------------------


class RequirementResultItem(BaseModel):
    requirement_result_id: uuid.UUID
    requirement_id: uuid.UUID
    requirement_title: str
    requirement_code: str
    requirement_type: str
    mandatory: bool
    compliance_status: str  # PASS / FAIL / PARTIAL / NOT_VERIFIED / NOT_APPLICABLE
    explanation: Optional[str] = None
    rule_results: Optional[List[Dict[str, Any]]] = None
    review: Optional[RequirementReviewRead] = None


# ---------------------------------------------------------------------------
# Full review payload
# ---------------------------------------------------------------------------


class ReviewPayloadResponse(BaseModel):
    evaluation_id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    evaluation_status: str
    summary: ComplianceSummaryRead
    review: Optional[OfficerReviewRead] = None
    requirements: List[RequirementResultItem] = []
