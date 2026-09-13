"""Compliance Engine for SecondLook (Task 11).

Deterministic, rules-based compliance evaluation layer (Layer 3).
Evaluates individual tender requirements against verified evidence.
Produces factual requirement-level evaluations without making final bidder decisions.

NO LLM calls. NO automated qualification/disqualification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Evidence:
    """Standardized verified evidence item for compliance evaluation."""

    source: str  # e.g. "GST", "PAN", "UDYAM", "DOCUMENT"
    identifier: Optional[str] = None
    verified: bool = False
    verification_id: Optional[str] = None
    document_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleResult:
    """Outcome of evaluating a single rule within a requirement."""

    rule_index: int
    field: str
    operator: str
    expected: Any
    actual: Any
    passed: bool
    status: str  # PASS, FAIL, NOT_VERIFIED
    reason: str


@dataclass
class RequirementResult:
    """Outcome of evaluating a tender requirement against available evidence."""

    status: str  # PASS, FAIL, PARTIAL, NOT_VERIFIED, NOT_APPLICABLE
    summary: str
    explanation: str
    rule_results: List[RuleResult] = field(default_factory=list)
    evidence_used: List[Dict[str, Any]] = field(default_factory=list)


def normalize_text(value: Any) -> str:
    """Normalize text by stripping, uppercasing, and collapsing whitespace."""
    if value is None:
        return ""
    text = str(value).strip()
    return re.sub(r"\s+", " ", text).upper()


def normalize_date(value: Any) -> Optional[str]:
    """Attempt to normalize date to YYYY-MM-DD string."""
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return s


class ComplianceEngine:
    """Deterministic, rule-based evaluation engine for tender requirements."""

    SUPPORTED_OPERATORS = {
        "EQUALS",
        "STATUS_EQUALS",
        "FIELD_EQUALS",
        "FIELD_EXISTS",
        "FIELD_NOT_EMPTY",
        "IDENTIFIER_MATCH",
        "FIELD_GREATER_THAN_OR_EQUAL",
        "GREATER_THAN_OR_EQUAL",
    }

    @staticmethod
    def evaluate_rule(
        rule: Dict[str, Any],
        evidence_list: List[Evidence],
        rule_index: int = 0,
    ) -> RuleResult:
        """Evaluate an individual rule against available evidence.

        A rule is defined as:
        {
            "source": "GST",
            "field": "status",
            "operator": "STATUS_EQUALS",  # or EQUALS, FIELD_EQUALS, FIELD_EXISTS, FIELD_NOT_EMPTY, IDENTIFIER_MATCH, FIELD_GREATER_THAN_OR_EQUAL
            "expected_value": "ACTIVE"
        }
        """
        source = rule.get("source", "").strip().upper()
        target_field = rule.get("field", "").strip()
        raw_operator = rule.get("operator", "EQUALS").strip().upper()
        expected = rule.get("expected_value")

        # Map aliases
        operator = raw_operator
        if operator in ("STATUS_EQUALS", "FIELD_EQUALS"):
            operator = "EQUALS"
        elif operator == "FIELD_GREATER_THAN_OR_EQUAL":
            operator = "GREATER_THAN_OR_EQUAL"

        # Find matching evidence for this source
        matching_evidence = [e for e in evidence_list if e.source.upper() == source]

        if not matching_evidence:
            return RuleResult(
                rule_index=rule_index,
                field=target_field,
                operator=raw_operator,
                expected=expected,
                actual=None,
                passed=False,
                status="NOT_VERIFIED",
                reason=f"No {source} evidence available for verification.",
            )

        # Check if any matching evidence is verified
        verified_evidence = [e for e in matching_evidence if e.verified]
        if not verified_evidence:
            return RuleResult(
                rule_index=rule_index,
                field=target_field,
                operator=raw_operator,
                expected=expected,
                actual=None,
                passed=False,
                status="NOT_VERIFIED",
                reason=f"{source} evidence provided but is not government-verified.",
            )

        # Evaluate against the primary verified evidence
        ev = verified_evidence[0]
        data = ev.data or {}

        # ------------------------------------------------------------------
        # 1. IDENTIFIER_MATCH
        # ------------------------------------------------------------------
        if raw_operator == "IDENTIFIER_MATCH":
            actual_val = ev.identifier or data.get(target_field)
            if not actual_val:
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected=expected,
                    actual=None,
                    passed=False,
                    status="NOT_VERIFIED",
                    reason=f"Identifier for {source} is unavailable in verified record.",
                )
            if expected is None:
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected=None,
                    actual=actual_val,
                    passed=True,
                    status="PASS",
                    reason=f"{source} identifier {actual_val} verified against government record.",
                )
            norm_actual = normalize_text(actual_val)
            norm_expected = normalize_text(expected)
            passed = norm_actual == norm_expected
            return RuleResult(
                rule_index=rule_index,
                field=target_field,
                operator=raw_operator,
                expected=expected,
                actual=actual_val,
                passed=passed,
                status="PASS" if passed else "FAIL",
                reason=(
                    f"Identifier match verified ({actual_val} matches {expected})."
                    if passed
                    else f"Identifier mismatch: expected {expected}, verified evidence has {actual_val}."
                ),
            )

        # ------------------------------------------------------------------
        # 2. FIELD_EXISTS
        # Field exists with a valid value -> PASS.
        # Field missing because evidence/field is unavailable -> NOT_VERIFIED.
        # ------------------------------------------------------------------
        if operator == "FIELD_EXISTS":
            exists = target_field in data and data[target_field] is not None
            if exists:
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected="FIELD_EXISTS",
                    actual="PRESENT",
                    passed=True,
                    status="PASS",
                    reason=f"Field '{target_field}' exists with valid value in verified {source} record.",
                )
            else:
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected="FIELD_EXISTS",
                    actual=None,
                    passed=False,
                    status="NOT_VERIFIED",
                    reason=f"Field '{target_field}' is unavailable in verified {source} record.",
                )

        # ------------------------------------------------------------------
        # 3. FIELD_NOT_EMPTY
        # Non-empty verified value -> PASS.
        # Unavailable field -> NOT_VERIFIED.
        # Explicitly verified empty value -> FAIL.
        # ------------------------------------------------------------------
        if operator == "FIELD_NOT_EMPTY":
            if target_field not in data or data.get(target_field) is None:
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected="NOT_EMPTY",
                    actual=None,
                    passed=False,
                    status="NOT_VERIFIED",
                    reason=f"Field '{target_field}' is unavailable in verified {source} record.",
                )
            val = data.get(target_field)
            if str(val).strip() != "":
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected="NOT_EMPTY",
                    actual=val,
                    passed=True,
                    status="PASS",
                    reason=f"Field '{target_field}' is present and non-empty ({val}).",
                )
            else:
                # Explicitly verified empty value
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected="NOT_EMPTY",
                    actual=val,
                    passed=False,
                    status="FAIL",
                    reason=f"Field '{target_field}' is explicitly empty in verified {source} record.",
                )

        # ------------------------------------------------------------------
        # 4. EQUALS / STATUS_EQUALS / FIELD_EQUALS
        # If field is unavailable in verified record -> NOT_VERIFIED.
        # If field value contradicts expected -> FAIL.
        # If field value matches expected -> PASS.
        # ------------------------------------------------------------------
        if operator == "EQUALS":
            if target_field not in data or data.get(target_field) is None:
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected=expected,
                    actual=None,
                    passed=False,
                    status="NOT_VERIFIED",
                    reason=f"Field '{target_field}' is unavailable in verified {source} record.",
                )

            val = data.get(target_field)
            norm_val = normalize_text(val)
            norm_exp = normalize_text(expected)

            passed = norm_val == norm_exp
            status = "PASS" if passed else "FAIL"
            reason = (
                f"Field '{target_field}' matches required value '{expected}' (actual: '{val}')."
                if passed
                else f"Field '{target_field}' expected '{expected}', but verified evidence is '{val}'."
            )
            return RuleResult(
                rule_index=rule_index,
                field=target_field,
                operator=raw_operator,
                expected=expected,
                actual=val,
                passed=passed,
                status=status,
                reason=reason,
            )

        # ------------------------------------------------------------------
        # 5. GREATER_THAN_OR_EQUAL / FIELD_GREATER_THAN_OR_EQUAL
        # Numeric comparison: actual >= expected -> PASS, actual < expected -> FAIL
        # Missing/unparseable -> NOT_VERIFIED
        # ------------------------------------------------------------------
        if operator == "GREATER_THAN_OR_EQUAL":
            if target_field not in data or data.get(target_field) is None:
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected=expected,
                    actual=None,
                    passed=False,
                    status="NOT_VERIFIED",
                    reason=f"Field '{target_field}' is unavailable in verified {source} record.",
                )

            val = data.get(target_field)
            try:
                # Handle numeric strings or floats (e.g. "65%", "65.0", 65)
                clean_val_str = str(val).rstrip("%").strip()
                clean_exp_str = str(expected).rstrip("%").strip()
                actual_num = float(clean_val_str)
                expected_num = float(clean_exp_str)
            except (ValueError, TypeError):
                return RuleResult(
                    rule_index=rule_index,
                    field=target_field,
                    operator=raw_operator,
                    expected=expected,
                    actual=val,
                    passed=False,
                    status="NOT_VERIFIED",
                    reason=f"Field '{target_field}' value '{val}' or expected '{expected}' is not a valid number.",
                )

            passed = actual_num >= expected_num
            status = "PASS" if passed else "FAIL"
            reason = (
                f"Field '{target_field}' ({actual_num}) meets required minimum threshold ({expected_num})."
                if passed
                else f"Field '{target_field}' ({actual_num}) is below required minimum threshold ({expected_num})."
            )
            return RuleResult(
                rule_index=rule_index,
                field=target_field,
                operator=raw_operator,
                expected=expected,
                actual=val,
                passed=passed,
                status=status,
                reason=reason,
            )

        # Unsupported operator fallback
        return RuleResult(
            rule_index=rule_index,
            field=target_field,
            operator=raw_operator,
            expected=expected,
            actual=None,
            passed=False,
            status="NOT_VERIFIED",
            reason=f"Unsupported rule operator: {raw_operator}.",
        )

    @classmethod
    def evaluate_requirement(
        cls,
        requirement_code: str,
        requirement_title: str,
        rule_configs: List[Dict[str, Any]],
        evidence_list: List[Evidence],
    ) -> RequirementResult:
        """Evaluate a full requirement (which contains one or more rules) against evidence.

        Deterministic AND semantics:
        - If rule_configs is empty -> NOT_APPLICABLE
        - If ANY rule FAIL -> FAIL (a verified contradictory rule MUST produce FAIL)
        - Else if ALL rules PASS -> PASS
        - Else if ALL rules NOT_VERIFIED -> NOT_VERIFIED
        - Else if ANY rule PASS and others NOT_VERIFIED -> PARTIAL
        - Else -> NOT_VERIFIED
        """
        if not rule_configs:
            return RequirementResult(
                status="NOT_APPLICABLE",
                summary=f"Requirement {requirement_code} has no rules defined.",
                explanation="No evaluation rules configured for this statutory requirement.",
                rule_results=[],
                evidence_used=[],
            )

        rule_results: List[RuleResult] = []
        evidence_used_map: Dict[str, Dict[str, Any]] = {}

        for idx, rule in enumerate(rule_configs):
            res = cls.evaluate_rule(rule, evidence_list, rule_index=idx)
            rule_results.append(res)

            # Collect evidence references used
            source = rule.get("source", "").strip().upper()
            for ev in evidence_list:
                if ev.source.upper() == source:
                    key = f"{ev.source}:{ev.identifier or ''}"
                    evidence_used_map[key] = {
                        "source": ev.source,
                        "identifier": ev.identifier,
                        "verified": ev.verified,
                        "verification_id": ev.verification_id,
                        "document_id": ev.document_id,
                    }

        pass_count = sum(1 for r in rule_results if r.status == "PASS")
        fail_count = sum(1 for r in rule_results if r.status == "FAIL")
        not_verified_count = sum(1 for r in rule_results if r.status == "NOT_VERIFIED")
        total_rules = len(rule_results)

        # Deterministic AND semantics:
        if fail_count > 0:
            overall_status = "FAIL"
            summary = f"Rule criteria failed against verified evidence ({fail_count} failed)."
        elif pass_count == total_rules:
            overall_status = "PASS"
            summary = f"All {total_rules} rule criteria satisfied by verified evidence."
        elif not_verified_count == total_rules:
            overall_status = "NOT_VERIFIED"
            summary = "No verified evidence available to evaluate this requirement."
        elif pass_count > 0 and not_verified_count > 0:
            overall_status = "PARTIAL"
            summary = f"Partially met: {pass_count} passed, {not_verified_count} unverified/unavailable."
        else:
            overall_status = "NOT_VERIFIED"
            summary = "Evaluation inconclusive based on available evidence."

        # Construct clear, factual explanation lines
        explanation_lines = [
            f"Requirement: {requirement_code} - {requirement_title}",
            f"Overall Status: {overall_status}",
            f"Summary: {summary}",
            "Rule details:",
        ]
        for r in rule_results:
            explanation_lines.append(
                f"  - [{r.status}] Field '{r.field}' ({r.operator}): {r.reason}"
            )

        return RequirementResult(
            status=overall_status,
            summary=summary,
            explanation="\n".join(explanation_lines),
            rule_results=rule_results,
            evidence_used=list(evidence_used_map.values()),
        )
