from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleConfigSchema(BaseModel):
    source: str = Field(..., description="Evidence source, e.g. GST, PAN")
    field: str = Field(..., description="Field to evaluate on evidence data")
    operator: str = Field(..., description="Operator: EQUALS, EXISTS, NOT_EMPTY, IDENTIFIER_MATCH")
    expected_value: Optional[Any] = Field(None, description="Expected value for comparison if required")


class TenderRequirementCreate(BaseModel):
    code: str = Field(..., description="Unique code e.g. REQ-GST-001")
    title: str = Field(..., description="Requirement title")
    description: Optional[str] = None
    type: str = Field("GST", description="Requirement category: GST, PAN, UDYAM, DOCUMENT, etc.")
    mandatory: bool = True
    display_order: int = 1
    rule_config: List[Dict[str, Any]] = Field(default_factory=list)


class TenderRequirementRead(BaseModel):
    id: uuid.UUID
    tender_id: uuid.UUID
    code: str
    title: str
    description: Optional[str] = None
    type: str
    mandatory: bool
    display_order: int
    rule_config: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class RuleResultSchema(BaseModel):
    rule_index: int
    field: str
    operator: str
    expected: Any
    actual: Any
    passed: bool
    reason: Optional[str] = None


class EvidenceRead(BaseModel):
    source: str
    identifier: Optional[str] = None
    verified: bool = False
    verification_id: Optional[str] = None
    document_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class RequirementEvaluationRead(BaseModel):
    id: Optional[uuid.UUID] = None
    requirement_id: uuid.UUID
    bidder_id: uuid.UUID
    tender_id: uuid.UUID
    requirement_code: Optional[str] = None
    requirement_title: Optional[str] = None
    requirement_type: Optional[str] = None
    mandatory: bool = True
    status: str  # PASS, FAIL, PARTIAL, NOT_VERIFIED, NOT_APPLICABLE
    result: Optional[Dict[str, Any]] = None
    rule_results: Optional[List[Dict[str, Any]]] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    evaluated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ComplianceSummary(BaseModel):
    total_requirements: int = 0
    pass_count: int = 0
    fail_count: int = 0
    partial_count: int = 0
    not_verified_count: int = 0
    not_applicable_count: int = 0
    mandatory_failed: int = 0
    mandatory_not_verified: int = 0


DEFAULT_COMPLIANCE_DISCLAIMER = (
    "This compliance evaluation is an automated factual verification of individual statutory "
    "requirements based on submitted and verified evidence. It does not constitute an approval, "
    "rejection, qualification, or disqualification of the bidder. The procurement officer retains "
    "full authority and discretion for all procurement decisions."
)


class BidderComplianceResponse(BaseModel):
    tender_id: str
    bidder_id: str
    bidder_legal_name: Optional[str] = None
    summary: ComplianceSummary
    requirements: List[RequirementEvaluationRead] = Field(default_factory=list)
    disclaimer: str = DEFAULT_COMPLIANCE_DISCLAIMER
