from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_bidders: int = 0
    evaluated: int = 0
    not_started: int = 0
    processing: int = 0
    completed: int = 0
    attention_required: int = 0
    reviews_completed: int = 0
    reviews_pending: int = 0


class BidderDashboard(BaseModel):
    bidder_id: str
    bidder_name: str
    evaluation_status: str = "NOT_STARTED"
    total_requirements: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    not_verified: int = 0
    not_applicable: int = 0
    compliance_percentage: float = 0.0
    review_status: str = "NOT_STARTED"
    officer_decision: str = "NO_DECISION"
    attention_required: bool = False
    attention_reasons: List[str] = Field(default_factory=list)


class RequirementIssue(BaseModel):
    requirement_id: str
    title: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    not_verified: int = 0
    not_applicable: int = 0


class TenderDashboard(BaseModel):
    tender: Dict[str, Any]
    summary: DashboardSummary
    bidders: List[BidderDashboard]
    requirement_issues: List[RequirementIssue]
