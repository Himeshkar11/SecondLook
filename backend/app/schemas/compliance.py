from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

VALID_REQUIREMENT_STATUSES = {
    "DRAFT",
    "AI_SUGGESTED",
    "UNDER_REVIEW",
    "APPROVED",
    "REJECTED",
    "ARCHIVED",
}

VALID_REQUIREMENT_TYPES = {
    "GST",
    "PAN",
    "UDYAM",
    "MSME",
    "FINANCIAL",
    "EXPERIENCE",
    "TECHNICAL",
    "DOCUMENT",
    "OEM",
    "MAKE_IN_INDIA",
    "EPFO",
    "ESIC",
    "STARTUP_INDIA",
    "NSIC",
    "BLACKLISTING",
    "OTHER",
}


class RuleConfigSchema(BaseModel):
    source: str = Field(..., description="Evidence source, e.g. GST, PAN")
    field: str = Field(..., description="Field to evaluate on evidence data")
    operator: str = Field(..., description="Operator: EQUALS, EXISTS, NOT_EMPTY, IDENTIFIER_MATCH")
    expected_value: Optional[Any] = Field(None, description="Expected value for comparison if required")


class TenderRequirementCreate(BaseModel):
    code: Optional[str] = Field(None, description="Unique code e.g. REQ-GST-001 (auto-generated if omitted)")
    title: str = Field(..., description="Requirement title")
    description: Optional[str] = None
    type: str = Field("GST", description="Requirement category: GST, PAN, UDYAM, DOCUMENT, etc.")
    mandatory: bool = True
    display_order: int = 1
    status: str = Field("UNDER_REVIEW", description="Initial status: DRAFT or UNDER_REVIEW")
    rule_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    rule_config: List[Dict[str, Any]] = Field(default_factory=list)
    source_document_id: Optional[uuid.UUID] = None
    source_text: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    rejection_reason: Optional[str] = None


class TenderRequirementUpdate(BaseModel):
    """Schema for updating a tender requirement.

    NOTE: Direct escalation to APPROVED via normal update is strictly rejected by the backend.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    mandatory: Optional[bool] = None
    display_order: Optional[int] = None
    rule_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    rule_config: Optional[List[Dict[str, Any]]] = None
    source_text: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    status: Optional[str] = Field(None, description="Cannot be set to APPROVED via generic update")


class TenderRequirementRead(BaseModel):
    id: uuid.UUID
    tender_id: uuid.UUID
    code: str
    title: str
    description: Optional[str] = None
    type: str
    mandatory: bool
    display_order: int
    status: str = "APPROVED"
    rule_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    rule_config: List[Dict[str, Any]] = Field(default_factory=list)
    source_document_id: Optional[uuid.UUID] = None
    source_text: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    approved_by: Optional[uuid.UUID] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    approved_at: Optional[Any] = None

    model_config = {"from_attributes": True}


class TenderExtractionRequest(BaseModel):
    text: Optional[str] = Field(None, description="Raw text of the tender to extract from")
    document_id: Optional[str] = Field(None, description="Document ID of an uploaded tender document")


class TenderExtractionResponse(BaseModel):
    tender_id: str
    extracted_count: int
    requirements: List[TenderRequirementRead] = Field(default_factory=list)


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
    evaluation_id: Optional[uuid.UUID] = None
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
    mandatory_total: int = 0
    mandatory_passed: int = 0
    optional_total: int = 0
    optional_passed: int = 0
    optional_failed: int = 0
    optional_not_verified: int = 0


DEFAULT_COMPLIANCE_DISCLAIMER = (
    "This compliance evaluation is an automated factual verification of individual statutory "
    "requirements based on submitted and verified evidence. It does not constitute an approval, "
    "rejection, qualification, or disqualification of the bidder. The procurement officer retains "
    "full authority and discretion for all procurement decisions."
)


class BidderComplianceResponse(BaseModel):
    evaluation_id: Optional[str] = None
    tender_id: str
    bidder_id: str
    bidder_legal_name: Optional[str] = None
    summary: ComplianceSummary
    requirements: List[RequirementEvaluationRead] = Field(default_factory=list)
    disclaimer: str = DEFAULT_COMPLIANCE_DISCLAIMER


class ComplianceEvaluationRead(BaseModel):
    evaluation_id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    bidder_legal_name: Optional[str] = None
    tender_title: Optional[str] = None
    status: str = "COMPLETED"  # PENDING, PROCESSING, COMPLETED, FAILED
    summary: ComplianceSummary
    requirements: List[RequirementEvaluationRead] = Field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    disclaimer: str = DEFAULT_COMPLIANCE_DISCLAIMER

    model_config = {"from_attributes": True}


class ComplianceEvaluationSummaryItem(BaseModel):
    evaluation_id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    status: str
    summary: Optional[Dict[str, Any]] = None
    created_at: str
    model_config = {"from_attributes": True}


class FieldComparisonRead(BaseModel):
    field: str
    expected_value: Optional[Any] = None
    document_value: Optional[Any] = None
    government_value: Optional[Any] = None
    result: str = "MATCH"  # MATCH, MISMATCH, UNAVAILABLE


class NormalizedEvidenceItemRead(BaseModel):
    evidence_id: str
    source_type: str
    source: str
    document_id: Optional[str] = None
    verification_id: Optional[str] = None
    extraction_id: Optional[str] = None
    field: Optional[str] = None
    value: Optional[Any] = None
    expected_value: Optional[Any] = None
    document_value: Optional[Any] = None
    government_value: Optional[Any] = None
    result: Optional[str] = None
    retrieved_at: Optional[str] = None
    is_demo: bool = True
    verified: bool = False
    field_comparisons: List[FieldComparisonRead] = Field(default_factory=list)
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    ai_extracted: Dict[str, Any] = Field(default_factory=dict)
    conflict_detected: bool = False
    conflict_details: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceTraceChainRead(BaseModel):
    requirement_id: str
    requirement_code: str
    requirement_title: str
    evaluation_id: Optional[str] = None
    evaluation_status: str = "NOT_VERIFIED"
    explanation: str = ""
    rule_results: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[NormalizedEvidenceItemRead] = Field(default_factory=list)
    document_trace: Optional[Dict[str, Any]] = None
    ocr_trace: Optional[Dict[str, Any]] = None
    ai_trace: Optional[Dict[str, Any]] = None
    government_trace: Optional[Dict[str, Any]] = None


class EvaluationEvidenceTraceResponse(BaseModel):
    evaluation_id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    traces: List[EvidenceTraceChainRead] = Field(default_factory=list)
