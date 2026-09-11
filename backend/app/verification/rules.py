"""Rule evaluation abstractions and deterministic demo rules.

This module defines individual compliance rules and the RulesEngine.
It does not contain pipeline orchestration, scoring math, or risk logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.extractor import StructuredDocumentData
from app.integrations.base import IntegrationResponse, IntegrationStatus


class RuleEvaluationResult(BaseModel):
    """Normalized outcome for a single compliance rule evaluation."""

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    passed: bool = Field(..., description="Whether the rule passed or failed")
    message: str = Field(..., description="Evaluation description or reason for outcome")
    details: Dict[str, Any] = Field(default_factory=dict, description="Rule-specific diagnostic details")


class Rule(ABC):
    """Abstract interface representing a single compliance verification rule."""

    rule_id: str
    name: str

    @abstractmethod
    def evaluate(
        self,
        extracted_data: StructuredDocumentData,
        verification_data: IntegrationResponse,
    ) -> RuleEvaluationResult:
        """Evaluate the rule against extracted document data and external verification data."""
        raise NotImplementedError("Rules must implement evaluate(...)")


class DocumentTypeRule(Rule):
    """Rule verifying that a valid document type was identified."""

    rule_id = "RULE_DOC_TYPE"
    name = "Document Type Identified"

    def evaluate(
        self,
        extracted_data: StructuredDocumentData,
        verification_data: IntegrationResponse,
    ) -> RuleEvaluationResult:
        doc_type = (extracted_data.document_type or "").strip()
        passed = bool(doc_type and doc_type != "UNKNOWN")
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            name=self.name,
            passed=passed,
            message="Document type was identified" if passed else "Document type is missing or unknown",
            details={"document_type": doc_type},
        )


class DocumentNumberRule(Rule):
    """Rule verifying that a primary registration/document number is present."""

    rule_id = "RULE_DOC_NUMBER"
    name = "Document Number Present"

    def evaluate(
        self,
        extracted_data: StructuredDocumentData,
        verification_data: IntegrationResponse,
    ) -> RuleEvaluationResult:
        doc_num = (extracted_data.document_number or "").strip()
        passed = bool(doc_num)
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            name=self.name,
            passed=passed,
            message="Primary document identifier found" if passed else "Document identifier is missing",
            details={"document_number": doc_num},
        )


class LegalNamePresentRule(Rule):
    """Rule verifying that legal entity name exists on the document."""

    rule_id = "RULE_LEGAL_NAME"
    name = "Legal Name Present"

    def evaluate(
        self,
        extracted_data: StructuredDocumentData,
        verification_data: IntegrationResponse,
    ) -> RuleEvaluationResult:
        legal_name = (extracted_data.legal_name or "").strip()
        passed = bool(legal_name)
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            name=self.name,
            passed=passed,
            message="Legal entity name found" if passed else "Legal entity name is missing",
            details={"legal_name": legal_name},
        )


class GovernmentStatusRule(Rule):
    """Rule verifying that statutory integration returned an acceptable verification status."""

    rule_id = "RULE_GOV_STATUS"
    name = "Government Verification Status"

    def evaluate(
        self,
        extracted_data: StructuredDocumentData,
        verification_data: IntegrationResponse,
    ) -> RuleEvaluationResult:
        acceptable_statuses = {
            IntegrationStatus.VERIFIED.value,
            IntegrationStatus.CLEAR.value,
        }
        passed = verification_data.success and verification_data.status in acceptable_statuses
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            name=self.name,
            passed=passed,
            message=(
                f"Statutory provider returned valid status: {verification_data.status}"
                if passed
                else f"Statutory provider status not acceptable: {verification_data.status}"
            ),
            details={
                "provider": verification_data.provider,
                "status": verification_data.status,
                "success": verification_data.success,
            },
        )


class RegistrationStatusRule(Rule):
    """Rule verifying that document registration status is active."""

    rule_id = "RULE_REGISTRATION_STATUS"
    name = "Registration Status Active"

    def evaluate(
        self,
        extracted_data: StructuredDocumentData,
        verification_data: IntegrationResponse,
    ) -> RuleEvaluationResult:
        status = (extracted_data.registration_status or "").strip().upper()
        passed = status in {"ACTIVE", "VALID", "REGULAR"}
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            name=self.name,
            passed=passed,
            message=f"Registration status is {status}" if passed else f"Registration status {status} is not active",
            details={"registration_status": status},
        )


class RulesEngine:
    """Coordinates evaluation of compliance rules.

    Permits custom rule lists via dependency injection or defaults to
    the standard deterministic demo compliance ruleset.
    """

    def __init__(self, rules: Optional[List[Rule]] = None) -> None:
        self.rules = rules if rules is not None else [
            DocumentTypeRule(),
            DocumentNumberRule(),
            LegalNamePresentRule(),
            GovernmentStatusRule(),
            RegistrationStatusRule(),
        ]

    def evaluate(
        self,
        extracted_data: StructuredDocumentData,
        verification_data: IntegrationResponse,
    ) -> List[RuleEvaluationResult]:
        """Evaluate all registered rules in deterministic order."""
        return [rule.evaluate(extracted_data, verification_data) for rule in self.rules]
