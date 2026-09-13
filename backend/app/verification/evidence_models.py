"""Normalized Evidence Models for SecondLook Traceability (Task 15).

Provides standard representations for field-level traceable compliance evidence,
supporting multi-source auditability across DOCUMENT, OCR, AI_EXTRACTION, and
GOVERNMENT_VERIFICATION layers.
"""

from __future__ import annotations

import dataclasses
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceType(str, Enum):
    """Supported evidence types in the SecondLook compliance pipeline."""

    DOCUMENT = "DOCUMENT"
    OCR = "OCR"
    AI_EXTRACTION = "AI_EXTRACTION"
    GOVERNMENT_VERIFICATION = "GOVERNMENT_VERIFICATION"


@dataclass
class FieldComparisonItem:
    """Individual field-level comparison between document/AI and government records."""

    field: str
    expected_value: Any = None
    document_value: Any = None
    government_value: Any = None
    result: str = "MATCH"  # MATCH, MISMATCH, UNAVAILABLE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedEvidenceItem:
    """Standardized representation of an evidence item used in a compliance evaluation."""

    evidence_id: str
    source_type: str  # GOVERNMENT_VERIFICATION, AI_EXTRACTION, OCR, DOCUMENT
    source: str  # GST, PAN, UDYAM, EPFO, ESIC, STARTUP_INDIA, NSIC, MAKE_IN_INDIA, OEM, BLACKLIST
    document_id: Optional[str] = None
    verification_id: Optional[str] = None
    extraction_id: Optional[str] = None
    field: Optional[str] = None
    value: Any = None
    expected_value: Any = None
    document_value: Any = None
    government_value: Any = None
    result: Optional[str] = None  # MATCH, MISMATCH, VERIFIED, CLEAR, LISTED, NOT_VERIFIED, UNAVAILABLE
    retrieved_at: Optional[str] = None
    is_demo: bool = True
    verified: bool = False
    field_comparisons: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    raw_data: Dict[str, Any] = dataclasses.field(default_factory=dict)
    ai_extracted: Dict[str, Any] = dataclasses.field(default_factory=dict)
    conflict_detected: bool = False
    conflict_details: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "source": self.source,
            "document_id": self.document_id,
            "verification_id": self.verification_id,
            "extraction_id": self.extraction_id,
            "field": self.field,
            "value": self.value,
            "expected_value": self.expected_value,
            "document_value": self.document_value,
            "government_value": self.government_value,
            "result": self.result,
            "retrieved_at": self.retrieved_at,
            "is_demo": self.is_demo,
            "verified": self.verified,
            "field_comparisons": self.field_comparisons,
            "raw_data": self.raw_data,
            "ai_extracted": self.ai_extracted,
            "conflict_detected": self.conflict_detected,
            "conflict_details": self.conflict_details,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


@dataclass
class EvidenceTraceChain:
    """Full hierarchical trace chain connecting requirement to original secure document."""

    requirement_id: str
    requirement_code: str
    requirement_title: str
    rule_results: List[Dict[str, Any]]
    evaluation_id: Optional[str] = None
    evaluation_status: str = "NOT_VERIFIED"  # PASS, FAIL, PARTIAL, NOT_VERIFIED
    explanation: str = ""
    evidence_items: List[NormalizedEvidenceItem] = dataclasses.field(default_factory=list)
    document_trace: Optional[Dict[str, Any]] = None
    ocr_trace: Optional[Dict[str, Any]] = None
    ai_trace: Optional[Dict[str, Any]] = None
    government_trace: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "requirement_code": self.requirement_code,
            "requirement_title": self.requirement_title,
            "rule_results": self.rule_results,
            "evaluation_id": self.evaluation_id,
            "evaluation_status": self.evaluation_status,
            "explanation": self.explanation,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "document_trace": self.document_trace,
            "ocr_trace": self.ocr_trace,
            "ai_trace": self.ai_trace,
            "government_trace": self.government_trace,
        }
