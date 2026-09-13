"""Bidder-facing compliance visibility schemas (Milestone 09).

Exposes factual evaluation outcomes, deterministic compliance score,
explanations, and evidence references while strictly excluding officer-only
notes, decisions, and internal administrative audit trails.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BidderComplianceRequirementItem(BaseModel):
    """Bidder-safe presentation of an individual evaluated requirement."""

    requirement_id: UUID = Field(..., description="Unique identifier of the tender requirement")
    requirement_code: str = Field(..., description="Requirement code e.g. REQ-GST-001")
    requirement_title: str = Field(..., description="Human-readable title of the requirement")
    requirement_type: Optional[str] = Field(None, description="Category of requirement e.g. GST, PAN, TECHNICAL")
    mandatory: bool = Field(..., description="Whether this requirement is mandatory for evaluation")
    status: str = Field(..., description="Evaluation outcome: PASS, FAIL, PARTIAL, NOT_VERIFIED, NOT_APPLICABLE")
    explanation: Optional[str] = Field(None, description="Factual, deterministic explanation of the evaluation result")
    evidence_sources: List[str] = Field(default_factory=list, description="List of evidence sources evaluated")
    has_evidence: bool = Field(..., description="Whether evidence was resolved for this requirement")
    document_id: Optional[str] = Field(None, description="Associated document ID if available for secure access")
    actionable_guidance: Optional[str] = Field(None, description="Remediation guidance if requirement did not pass")


class BidderComplianceSummary(BaseModel):
    """Aggregate statistics for a compliance evaluation run."""

    total_requirements: int = Field(..., description="Total number of evaluated tender requirements")
    applicable_count: int = Field(..., description="Total requirements excluding NOT_APPLICABLE")
    pass_count: int = Field(..., description="Count of requirements with status PASS")
    fail_count: int = Field(..., description="Count of requirements with status FAIL")
    partial_count: int = Field(..., description="Count of requirements with status PARTIAL")
    not_verified_count: int = Field(..., description="Count of requirements with status NOT_VERIFIED")
    not_applicable_count: int = Field(..., description="Count of requirements with status NOT_APPLICABLE")
    mandatory_total: int = Field(..., description="Total mandatory requirements")
    mandatory_passed: int = Field(..., description="Mandatory requirements passed")
    mandatory_failed: int = Field(..., description="Mandatory requirements failed")
    mandatory_not_verified: int = Field(..., description="Mandatory requirements not verified")
    optional_total: int = Field(..., description="Total optional requirements")
    optional_passed: int = Field(..., description="Optional requirements passed")
    optional_failed: int = Field(..., description="Optional requirements failed")
    optional_not_verified: int = Field(..., description="Optional requirements not verified")


class BidderComplianceViewResponse(BaseModel):
    """Top-level bidder response for bid compliance evaluation."""

    bid_id: UUID = Field(..., description="Unique ID of the bid workspace")
    tender_id: UUID = Field(..., description="Unique ID of the tender")
    bidder_id: UUID = Field(..., description="Unique ID of the bidder profile")
    tender_title: Optional[str] = Field(None, description="Title of the tender")
    tender_reference_number: Optional[str] = Field(None, description="Public tender reference code")
    evaluation_id: Optional[UUID] = Field(None, description="UUID of the evaluation run if executed")
    status: str = Field(..., description="Evaluation state: NOT_EVALUATED, PENDING, PROCESSING, COMPLETED, FAILED")
    score: Optional[float] = Field(None, description="Deterministic compliance percentage (0-100) or None")
    score_formatted: str = Field(..., description="Display string for compliance score e.g. '82.5%' or '—'")
    summary: Optional[BidderComplianceSummary] = Field(None, description="Aggregated requirement counts")
    requirements: List[BidderComplianceRequirementItem] = Field(default_factory=list, description="Evaluated requirement items")
    disclaimer: str = Field(..., description="Statutory non-qualification legal boundary notice")
    completed_at: Optional[str] = Field(None, description="Evaluation completion timestamp")
    created_at: Optional[str] = Field(None, description="Evaluation run initiation timestamp")
    message: Optional[str] = Field(None, description="Informational message regarding evaluation state")


class BidderComplianceHistoryItem(BaseModel):
    """Historical record of an evaluation run for a bidder and tender."""

    evaluation_id: UUID = Field(..., description="Unique UUID of this evaluation run")
    status: str = Field(..., description="Status of the evaluation run")
    score: Optional[float] = Field(None, description="Deterministic compliance score")
    score_formatted: str = Field(..., description="Formatted score display")
    total_requirements: int = Field(..., description="Total requirements evaluated in this run")
    pass_count: int = Field(..., description="Passed requirements count")
    fail_count: int = Field(..., description="Failed requirements count")
    created_at: str = Field(..., description="Timestamp when evaluation was created")
    completed_at: Optional[str] = Field(None, description="Timestamp when evaluation completed")
