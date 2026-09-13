"""Deterministic Explanation Engine for SecondLook Compliance Traceability (Task 15).

Derives 100% deterministic, audit-grade explanations for rule and requirement outcomes.
NO LLM or AI generation is used in this module. All explanations are synthesized
strictly from rule parameters, evaluation statuses, and verified evidence snapshots.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from app.verification.compliance_engine import RuleResult, normalize_text
from app.verification.evidence_models import (
    EvidenceTraceChain,
    FieldComparisonItem,
    NormalizedEvidenceItem,
)

logger = logging.getLogger(__name__)


class ExplanationEngine:
    """Deterministic, rule-based explanation and traceability generator."""

    @classmethod
    def explain_rule(
        cls,
        rule_result: Union[RuleResult, Dict[str, Any]],
        evidence: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Derive a human-readable, deterministic explanation for a single rule evaluation."""
        if isinstance(rule_result, RuleResult):
            status = rule_result.status
            field = rule_result.field
            operator = rule_result.operator
            expected = rule_result.expected
            actual = rule_result.actual
            reason = rule_result.reason
        else:
            status = rule_result.get("status", "NOT_VERIFIED")
            field = rule_result.get("field", "")
            operator = rule_result.get("operator", "EQUALS")
            expected = rule_result.get("expected")
            actual = rule_result.get("actual")
            reason = rule_result.get("reason", "")

        src = (source or (evidence.get("source") if evidence else "") or "").strip().upper()

        # Check for error in evidence source
        if evidence and (evidence.get("status") == "ERROR" or evidence.get("error")):
            err = evidence.get("error") or "Service unreachable"
            return f"Government source '{src or 'EXTERNAL'}' returned an error ({err}); requirement cannot be verified."

        if status == "PASS":
            if src == "BLACKLIST":
                return "Debarment check confirmed entity is CLEAR with no adverse listings found in registry."
            if src == "OEM" and field in ("authorization_valid", "authorized", "status"):
                auth_code = (evidence.get("government_data") or {}).get("authorization_code") if evidence else None
                code_str = f" (Authorization code: {auth_code})" if auth_code else ""
                return f"OEM authorization verified for manufacturer{code_str}."
            if src == "MAKE_IN_INDIA" and field in ("local_content_percentage", "local_content"):
                return f"Make in India declaration verified: Local content is {actual}%, meeting or exceeding required threshold of {expected}%."
            if operator in ("FIELD_GREATER_THAN_OR_EQUAL", "GREATER_THAN_OR_EQUAL"):
                return f"Verified value for '{field}' ({actual}) meets or exceeds required minimum threshold ({expected})."
            if operator == "IDENTIFIER_MATCH":
                return f"Document identifier '{actual}' matches official government registry record."
            if operator in ("FIELD_EXISTS", "FIELD_NOT_EMPTY"):
                return f"Required field '{field}' is present with verified value '{actual}'."
            # Status / Equality match
            if operator in ("STATUS_EQUALS", "EQUALS", "FIELD_EQUALS"):
                return f"Government verification confirmed {src + ' ' if src else ''}{field} is '{actual}', matching expected requirement '{expected}'."
            return f"Rule criteria satisfied: {reason or 'Condition met.'}"

        if status == "FAIL":
            if src == "BLACKLIST" or (actual and normalize_text(actual) in ("LISTED", "DEBARRED", "BLACKLISTED")):
                details = (evidence.get("government_data") or {}).get("reason") if evidence else None
                reason_str = f" Reason: '{details}'." if details else ""
                return f"Entity is listed in debarment / blacklist registry (Status: {actual}).{reason_str}"
            if operator in ("FIELD_GREATER_THAN_OR_EQUAL", "GREATER_THAN_OR_EQUAL"):
                return f"Verified value for '{field}' ({actual}) is below required minimum threshold ({expected})."
            if operator == "IDENTIFIER_MATCH":
                return f"Document identifier '{actual}' does not match government record '{expected}'."
            if evidence and evidence.get("conflict_detected"):
                conflict = evidence.get("conflict_details") or {}
                ai_val = conflict.get("ai_extracted", "N/A")
                gov_val = conflict.get("government_verified", actual)
                return (
                    f"Evidence conflict detected: Document AI extracted {field} as '{ai_val}', "
                    f"but official government verification returned '{gov_val}'. Government record takes precedence."
                )
            if operator in ("STATUS_EQUALS", "EQUALS", "FIELD_EQUALS"):
                return f"Government record for {field} is '{actual}', which does not match required '{expected}'."
            return f"Rule criteria failed against verified evidence: {reason or 'Condition not met.'}"

        # NOT_VERIFIED
        if evidence:
            ai_data = evidence.get("ai_extracted") or evidence.get("ai_extracted_data")
            is_verified = evidence.get("verified", False)
            if ai_data and not is_verified:
                return (
                    f"Document data was extracted by AI, but external government verification has not been completed "
                    f"or confirmed for field '{field}'."
                )
        return (
            f"Evidence for field '{field}' is not available or has not been verified against government records."
        )

    @classmethod
    def build_field_comparisons(
        cls,
        rule_configs: List[Dict[str, Any]],
        rule_results: List[Union[RuleResult, Dict[str, Any]]],
        evidence_items: List[Dict[str, Any]],
    ) -> List[FieldComparisonItem]:
        """Construct detailed side-by-side field comparisons across Document, AI, and Government data."""
        comparisons: List[FieldComparisonItem] = []
        evidence_by_src = {
            (e.get("source") or "").strip().upper(): e for e in evidence_items if isinstance(e, dict)
        }

        for idx, rc in enumerate(rule_configs):
            field = rc.get("field", "")
            expected = rc.get("expected_value")
            source = (rc.get("source") or "").strip().upper()
            ev = evidence_by_src.get(source, {})

            gov_data = ev.get("government_data") or {}
            ai_data = ev.get("ai_extracted") or ev.get("ai_extracted_data") or {}

            doc_val = ai_data.get(field)
            gov_val = gov_data.get(field)

            # Match status from rule result
            rule_res = rule_results[idx] if idx < len(rule_results) else None
            status = "UNAVAILABLE"
            if rule_res:
                r_status = rule_res.status if isinstance(rule_res, RuleResult) else rule_res.get("status")
                if r_status == "PASS":
                    status = "MATCH"
                elif r_status == "FAIL":
                    status = "MISMATCH"
                else:
                    status = "UNAVAILABLE"

            comparisons.append(
                FieldComparisonItem(
                    field=field,
                    expected_value=expected,
                    document_value=doc_val,
                    government_value=gov_val,
                    result=status,
                )
            )

        return comparisons

    @classmethod
    def explain_requirement_evaluation(
        cls,
        requirement_code: str,
        requirement_title: str,
        status: str,
        rule_results: List[Union[RuleResult, Dict[str, Any]]],
        evidence_items: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate a complete, coherent explanation report for a requirement evaluation."""
        lines: List[str] = [
            f"Requirement: {requirement_code} - {requirement_title}",
            f"Overall Status: {status}",
        ]

        # Overall summary line
        if status == "PASS":
            lines.append(f"Summary: All rule criteria verified and confirmed by authoritative records.")
        elif status == "FAIL":
            fail_count = sum(
                1 for r in rule_results
                if (r.status if isinstance(r, RuleResult) else r.get("status")) == "FAIL"
            )
            lines.append(f"Summary: Rule criteria failed against verified evidence ({fail_count} failed).")
        elif status == "PARTIAL":
            lines.append("Summary: Requirement partially met; some criteria passed while others remain unverified.")
        elif status == "NOT_APPLICABLE":
            lines.append("Summary: No rules configured for this statutory requirement.")
        else:
            lines.append("Summary: Evidence unavailable or unverified for this requirement.")

        lines.append("Rule details:")
        ev_items = evidence_items or []
        for idx, r in enumerate(rule_results):
            r_status = r.status if isinstance(r, RuleResult) else r.get("status", "NOT_VERIFIED")
            r_field = r.field if isinstance(r, RuleResult) else r.get("field", "")
            r_op = r.operator if isinstance(r, RuleResult) else r.get("operator", "EQUALS")
            ev = ev_items[idx] if idx < len(ev_items) else (ev_items[0] if ev_items else None)

            explanation = cls.explain_rule(r, evidence=ev)
            lines.append(f"  - [{r_status}] Field '{r_field}' ({r_op}): {explanation}")

        return "\n".join(lines)

    @classmethod
    def build_trace_chain(
        cls,
        requirement_id: str,
        requirement_code: str,
        requirement_title: str,
        evaluation_status: str,
        rule_results: List[Dict[str, Any]],
        evidence_items: List[Dict[str, Any]],
        document_metadata: Optional[Dict[str, Any]] = None,
        ocr_metadata: Optional[Dict[str, Any]] = None,
        ai_metadata: Optional[Dict[str, Any]] = None,
        government_metadata: Optional[Dict[str, Any]] = None,
        evaluation_id: Optional[str] = None,
        document_trace: Optional[Dict[str, Any]] = None,
        ocr_trace: Optional[Dict[str, Any]] = None,
        ai_trace: Optional[Dict[str, Any]] = None,
        government_trace: Optional[Dict[str, Any]] = None,
    ) -> EvidenceTraceChain:
        """Assemble full end-to-end evidence trace chain from requirement to secure file."""
        doc_t = document_trace or document_metadata
        ocr_t = ocr_trace or ocr_metadata
        ai_t = ai_trace or ai_metadata
        gov_t = government_trace or government_metadata
        normalized_items: List[NormalizedEvidenceItem] = []
        for ev in evidence_items:
            source = ev.get("source", "UNKNOWN")
            is_verified = ev.get("verified", False)
            gov_data = ev.get("government_data") or {}
            ai_data = ev.get("ai_extracted") or ev.get("ai_extracted_data") or {}

            # Generate item
            item = NormalizedEvidenceItem(
                evidence_id=ev.get("verification_id") or ev.get("document_id") or str(requirement_id),
                source_type="GOVERNMENT_VERIFICATION" if is_verified else ("AI_EXTRACTION" if ai_data else "DOCUMENT"),
                source=source,
                document_id=ev.get("document_id"),
                verification_id=ev.get("verification_id"),
                field=ev.get("field"),
                value=ev.get("value"),
                retrieved_at=ev.get("retrieved_at") or ev.get("created_at"),
                is_demo=ev.get("is_demo", True),
                verified=is_verified,
                raw_data=gov_data,
                ai_extracted=ai_data,
                conflict_detected=ev.get("conflict_detected", False),
                conflict_details=ev.get("conflict_details"),
                explanation=ev.get("note"),
            )
            normalized_items.append(item)

        explanation = cls.explain_requirement_evaluation(
            requirement_code=requirement_code,
            requirement_title=requirement_title,
            status=evaluation_status,
            rule_results=rule_results,
            evidence_items=evidence_items,
        )

        return EvidenceTraceChain(
            requirement_id=requirement_id,
            requirement_code=requirement_code,
            requirement_title=requirement_title,
            rule_results=rule_results,
            evaluation_id=evaluation_id,
            evaluation_status=evaluation_status,
            explanation=explanation,
            evidence_items=normalized_items,
            document_trace=doc_t,
            ocr_trace=ocr_t,
            ai_trace=ai_t,
            government_trace=gov_t,
        )
