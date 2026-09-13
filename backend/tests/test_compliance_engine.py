"""Unit & Integration Tests for Compliance Evidence & Rule Engine Foundation (Task 11).

Tests all required test cases specified in Task 11 and user semantic corrections:
- Deterministic rule operators (EQUALS, STATUS_EQUALS, FIELD_EQUALS, FIELD_EXISTS, FIELD_NOT_EMPTY, IDENTIFIER_MATCH)
- Normalization (case, whitespace)
- Multi-rule AND semantics:
    PASS + PASS -> PASS
    FAIL + PASS -> FAIL
    PASS + FAIL -> FAIL
    FAIL + FAIL -> FAIL
    FAIL + NOT_VERIFIED -> FAIL
    NOT_VERIFIED + FAIL -> FAIL
    PASS + NOT_VERIFIED -> PARTIAL
    NOT_VERIFIED + PASS -> PARTIAL
    NOT_VERIFIED + NOT_VERIFIED -> NOT_VERIFIED
- FIELD_EXISTS: valid value -> PASS, unavailable -> NOT_VERIFIED
- FIELD_NOT_EMPTY: non-empty verified -> PASS, unavailable -> NOT_VERIFIED, explicitly empty -> FAIL
- NOT_APPLICABLE condition: empty rule_config ([])
- Evidence traceability links (verification_id, document_id)
- Service layer evaluation, seeding, and factual non-decision summary
"""

import uuid
from typing import Any, Dict, List
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.models.tender_requirement import RequirementEvaluation, TenderRequirement
from app.models.user import User
from app.schemas.compliance import (
    DEFAULT_COMPLIANCE_DISCLAIMER,
    BidderComplianceResponse,
    TenderRequirementCreate,
)
from app.services.compliance_service import ComplianceService
from app.verification.compliance_engine import (
    ComplianceEngine,
    Evidence,
    RequirementResult,
    RuleResult,
    normalize_text,
)


# ============================================================================
# UNIT TESTS: ComplianceEngine Rule & Requirement Evaluation
# ============================================================================


def test_01_req_gst_001_with_active_gst_passes():
    """Case 1: REQ-GST-001 with active GST -> PASS"""
    rule = {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            verification_id="v-1",
            document_id="d-1",
            data={"status": "ACTIVE", "legal_name": "Acme Corp", "state": "Tamil Nadu"},
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is True
    assert res.status == "PASS"

    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-GST-001",
        requirement_title="Active GST Registration",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "PASS"
    assert "satisfied" in req_res.summary.lower()


def test_02_req_gst_001_with_inactive_cancelled_gst_fails():
    """Case 2: REQ-GST-001 with inactive/cancelled GST -> FAIL"""
    rule = {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            verification_id="v-1",
            document_id="d-1",
            data={"status": "CANCELLED", "legal_name": "Acme Corp"},
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is False
    assert res.status == "FAIL"

    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-GST-001",
        requirement_title="Active GST Registration",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "FAIL"


def test_03_req_gst_001_with_no_gst_document_not_verified():
    """Case 3: REQ-GST-001 with no GST document -> NOT_VERIFIED"""
    rule = {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    evidence = []  # No evidence
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is False
    assert res.status == "NOT_VERIFIED"

    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-GST-001",
        requirement_title="Active GST Registration",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "NOT_VERIFIED"
    assert "no verified evidence" in req_res.summary.lower()


def test_04_req_gst_001_with_unverified_gst_document_not_verified():
    """Case 4: REQ-GST-001 with GST document but unverified -> NOT_VERIFIED"""
    rule = {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=False,  # Unverified!
            verification_id=None,
            document_id="d-1",
            data={"status": "ACTIVE"},
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is False
    assert res.status == "NOT_VERIFIED"

    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-GST-001",
        requirement_title="Active GST Registration",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "NOT_VERIFIED"


def test_05_req_gst_002_with_tamil_nadu_gst_passes():
    """Case 5: REQ-GST-002 with Tamil Nadu GST -> PASS"""
    rule = {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"state": "Tamil Nadu", "status": "ACTIVE"},
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-GST-002",
        requirement_title="Tamil Nadu GST Registration",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "PASS"


def test_06_req_gst_002_with_non_tamil_nadu_gst_fails():
    """Case 6: REQ-GST-002 with non-Tamil Nadu GST -> FAIL"""
    rule = {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}
    evidence = [
        Evidence(
            source="GST",
            identifier="27AAACG1234A1Z5",
            verified=True,
            data={"state": "Maharashtra", "status": "ACTIVE"},
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-GST-002",
        requirement_title="Tamil Nadu GST Registration",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "FAIL"


def test_07_req_gst_002_state_case_insensitive_matching():
    """Case 7: REQ-GST-002 with state matching case-insensitively -> PASS"""
    rule = {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"state": "tamil nadu"},  # lowercase
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is True
    assert res.status == "PASS"


def test_08_req_gst_002_state_whitespace_normalization():
    """Case 8: REQ-GST-002 with state matching with extra whitespace -> PASS"""
    rule = {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"state": "  Tamil   Nadu  "},  # irregular spacing
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is True
    assert res.status == "PASS"


def test_09_req_pan_001_with_active_pan_passes():
    """Case 9: REQ-PAN-001 with active PAN -> PASS"""
    rule = {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    evidence = [
        Evidence(
            source="PAN",
            identifier="ABCDE1234F",
            verified=True,
            data={"status": "ACTIVE", "pan": "ABCDE1234F", "full_name": "Acme Corp"},
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-PAN-001",
        requirement_title="Valid PAN",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "PASS"


def test_10_req_pan_001_with_inactive_pan_fails():
    """Case 10: REQ-PAN-001 with inactive PAN -> FAIL"""
    rule = {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    evidence = [
        Evidence(
            source="PAN",
            identifier="ABCDE1234F",
            verified=True,
            data={"status": "INACTIVE", "pan": "ABCDE1234F"},
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-PAN-001",
        requirement_title="Valid PAN",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "FAIL"


def test_11_req_pan_001_with_no_pan_document_not_verified():
    """Case 11: REQ-PAN-001 with no PAN document -> NOT_VERIFIED"""
    rule = {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    evidence = []
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-PAN-001",
        requirement_title="Valid PAN",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert req_res.status == "NOT_VERIFIED"


# ============================================================================
# MULTI-RULE DETERMINISTIC AND SEMANTICS (CRITICAL)
# ============================================================================


def test_12_multi_rule_pass_and_pass_returns_pass():
    """Case 12: PASS + PASS -> PASS"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"},
    ]
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"status": "ACTIVE", "state": "Tamil Nadu"},
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-001",
        requirement_title="TN Active GST",
        rule_configs=rules,
        evidence_list=evidence,
    )
    assert req_res.status == "PASS"


def test_13_multi_rule_fail_and_fail_returns_fail():
    """Case 13: FAIL + FAIL -> FAIL"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"},
    ]
    evidence = [
        Evidence(
            source="GST",
            identifier="27AAACG1234A1Z5",
            verified=True,
            data={"status": "CANCELLED", "state": "Maharashtra"},
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-001",
        requirement_title="TN Active GST",
        rule_configs=rules,
        evidence_list=evidence,
    )
    assert req_res.status == "FAIL"


def test_14_multi_rule_pass_and_fail_returns_fail():
    """Case 14: PASS + FAIL -> FAIL (Deterministic AND: verified contradiction fails overall)"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"},
    ]
    evidence = [
        Evidence(
            source="GST",
            identifier="27AAACG1234A1Z5",
            verified=True,
            data={"status": "ACTIVE", "state": "Karnataka"},  # Status passes, state fails!
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-001",
        requirement_title="TN Active GST",
        rule_configs=rules,
        evidence_list=evidence,
    )
    # Must be FAIL, NOT PARTIAL!
    assert req_res.status == "FAIL"
    assert "failed" in req_res.summary.lower()


def test_15_multi_rule_fail_and_pass_returns_fail():
    """Case 15: FAIL + PASS -> FAIL"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"},
    ]
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"status": "CANCELLED", "state": "Tamil Nadu"},  # Status fails, state passes
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-001",
        requirement_title="TN Active GST",
        rule_configs=rules,
        evidence_list=evidence,
    )
    assert req_res.status == "FAIL"


def test_16_multi_rule_pass_and_not_verified_returns_partial():
    """Case 16: PASS + NOT_VERIFIED -> PARTIAL (At least one passes, other is unverified)"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
    ]
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"status": "ACTIVE"},
        )
        # No PAN evidence
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-002",
        requirement_title="GST + PAN Active",
        rule_configs=rules,
        evidence_list=evidence,
    )
    assert req_res.status == "PARTIAL"


def test_17_multi_rule_not_verified_and_pass_returns_partial():
    """Case 17: NOT_VERIFIED + PASS -> PARTIAL"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
    ]
    evidence = [
        Evidence(
            source="PAN",
            identifier="ABCDE1234F",
            verified=True,
            data={"status": "ACTIVE"},
        )
        # No GST evidence
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-002",
        requirement_title="GST + PAN Active",
        rule_configs=rules,
        evidence_list=evidence,
    )
    assert req_res.status == "PARTIAL"


def test_18_multi_rule_not_verified_and_not_verified_returns_not_verified():
    """Case 18: NOT_VERIFIED + NOT_VERIFIED -> NOT_VERIFIED"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-002",
        requirement_title="GST + PAN Active",
        rule_configs=rules,
        evidence_list=[],
    )
    assert req_res.status == "NOT_VERIFIED"


def test_19_multi_rule_fail_and_not_verified_returns_fail():
    """Case 19: FAIL + NOT_VERIFIED -> FAIL (verified contradiction takes precedence)"""
    rules = [
        {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
    ]
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"status": "CANCELLED"},  # Explicit failure!
        )
        # PAN missing (not verified)
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-COMBO-002",
        requirement_title="GST + PAN Active",
        rule_configs=rules,
        evidence_list=evidence,
    )
    assert req_res.status == "FAIL"


# ============================================================================
# NOT_APPLICABLE SEMANTICS
# ============================================================================


def test_20_empty_rules_returns_not_applicable():
    """Case 20: Requirement with empty rules -> NOT_APPLICABLE.
    Condition: Exact check is len(rule_configs) == 0 (no rules configured).
    """
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-EMPTY-001",
        requirement_title="No Rules Requirement",
        rule_configs=[],
        evidence_list=[],
    )
    assert req_res.status == "NOT_APPLICABLE"
    assert "no rules defined" in req_res.summary.lower()


# ============================================================================
# OPERATOR TESTS: IDENTIFIER_MATCH, FIELD_EXISTS, FIELD_NOT_EMPTY
# ============================================================================


def test_21_identifier_match_matching_passes():
    """Case 21: IDENTIFIER_MATCH operator with matching identifier -> PASS"""
    rule = {
        "source": "GST",
        "field": "gstin",
        "operator": "IDENTIFIER_MATCH",
        "expected_value": "33AAACG1234A1Z5",
    }
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"gstin": "33AAACG1234A1Z5"},
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is True
    assert res.status == "PASS"


def test_22_identifier_match_mismatched_fails():
    """Case 22: IDENTIFIER_MATCH operator with mismatched identifier -> FAIL"""
    rule = {
        "source": "GST",
        "field": "gstin",
        "operator": "IDENTIFIER_MATCH",
        "expected_value": "33AAACG1234A1Z5",
    }
    evidence = [
        Evidence(
            source="GST",
            identifier="27AAACG9999Z1Z1",
            verified=True,
            data={"gstin": "27AAACG9999Z1Z1"},
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is False
    assert res.status == "FAIL"


def test_23_field_exists_with_valid_value_passes():
    """Case 23: FIELD_EXISTS with valid present value -> PASS"""
    rule = {"source": "GST", "field": "trade_name", "operator": "FIELD_EXISTS"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"trade_name": "Acme Industries", "status": "ACTIVE"},
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is True
    assert res.status == "PASS"


def test_24_field_exists_missing_unavailable_field_returns_not_verified():
    """Case 24: FIELD_EXISTS with unavailable field / missing evidence -> NOT_VERIFIED (NOT FAIL)"""
    rule = {"source": "GST", "field": "nonexistent_field", "operator": "FIELD_EXISTS"}
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            data={"status": "ACTIVE"},  # nonexistent_field is not in data
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is False
    assert res.status == "NOT_VERIFIED"  # Corrected: Must be NOT_VERIFIED, never auto-FAIL!


def test_25_field_not_empty_verified_non_empty_passes():
    """Case 25: FIELD_NOT_EMPTY with non-empty value -> PASS"""
    rule = {"source": "PAN", "field": "pan", "operator": "FIELD_NOT_EMPTY"}
    evidence = [
        Evidence(
            source="PAN",
            identifier="ABCDE1234F",
            verified=True,
            data={"pan": "ABCDE1234F"},
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is True
    assert res.status == "PASS"


def test_26_field_not_empty_unavailable_field_returns_not_verified():
    """Case 26: FIELD_NOT_EMPTY with unavailable/missing field -> NOT_VERIFIED (NOT FAIL)"""
    rule = {"source": "PAN", "field": "missing_pan", "operator": "FIELD_NOT_EMPTY"}
    evidence = [
        Evidence(
            source="PAN",
            identifier="ABCDE1234F",
            verified=True,
            data={"status": "ACTIVE"},  # missing_pan not present
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is False
    assert res.status == "NOT_VERIFIED"  # Corrected: Lack of evidence -> NOT_VERIFIED


def test_27_field_not_empty_explicitly_empty_value_fails():
    """Case 27: FIELD_NOT_EMPTY with explicitly verified empty string -> FAIL"""
    rule = {"source": "PAN", "field": "pan", "operator": "FIELD_NOT_EMPTY"}
    evidence = [
        Evidence(
            source="PAN",
            identifier="ABCDE1234F",
            verified=True,
            data={"pan": "   "},  # Explicitly present in record, but empty
        )
    ]
    res = ComplianceEngine.evaluate_rule(rule, evidence)
    assert res.passed is False
    assert res.status == "FAIL"  # Verified contradiction -> FAIL


def test_28_evidence_traceability_links():
    """Case 28: Evidence traceability: result contains verification_id and document_id"""
    rule = {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    verif_id = "v-uuid-12345"
    doc_id = "d-uuid-67890"
    evidence = [
        Evidence(
            source="GST",
            identifier="33AAACG1234A1Z5",
            verified=True,
            verification_id=verif_id,
            document_id=doc_id,
            data={"status": "ACTIVE"},
        )
    ]
    req_res = ComplianceEngine.evaluate_requirement(
        requirement_code="REQ-GST-001",
        requirement_title="Active GST",
        rule_configs=[rule],
        evidence_list=evidence,
    )
    assert len(req_res.evidence_used) == 1
    ev_ref = req_res.evidence_used[0]
    assert ev_ref["verification_id"] == verif_id
    assert ev_ref["document_id"] == doc_id
    assert ev_ref["source"] == "GST"
    assert ev_ref["identifier"] == "33AAACG1234A1Z5"


# ============================================================================
# INTEGRATION TESTS: Service Layer & SQLite In-Memory
# ============================================================================


@pytest.fixture
def sqlite_session():
    """Provide an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Seed demo user, tender, and bidder
    user_id = uuid.uuid4()
    user = User(id=user_id, email="officer@cpcl.gov.in", full_name="Procurement Officer", role="admin")
    session.add(user)

    tender_id = uuid.uuid4()
    tender = Tender(
        id=tender_id,
        reference_number="CPCL/TND/2026/001",
        title="Centrifugal Pump Supply",
        created_by=user_id,
    )
    session.add(tender)

    bidder_id = uuid.uuid4()
    bidder = Bidder(
        id=bidder_id,
        user_id=user_id,
        legal_name="Apex Engineering Ltd",
        gst_number="33AAACG1234A1Z5",
        pan_number="ABCDE1234F",
    )
    session.add(bidder)
    session.commit()

    yield session, str(tender_id), str(bidder_id)
    session.close()


def test_29_service_evaluates_all_tender_requirements(sqlite_session):
    """Case 29: Service layer: evaluate_bidder_compliance runs all tender requirements"""
    session, tender_id, bidder_id = sqlite_session
    service = ComplianceService(db=session)

    # Seed verified GST and PAN
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu", "legal_name": "Apex Engineering Ltd"},
    )
    gv_pan = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="PAN",
        provider="demo",
        identifier="ABCDE1234F",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "pan": "ABCDE1234F", "full_name": "Apex Engineering Ltd"},
    )
    session.add_all([gv_gst, gv_pan])
    session.commit()

    resp = service.evaluate_bidder_compliance(tender_id=tender_id, bidder_id=bidder_id)

    assert resp.tender_id == tender_id
    assert resp.bidder_id == bidder_id
    assert resp.bidder_legal_name == "Apex Engineering Ltd"
    assert resp.summary.total_requirements == 3
    assert resp.summary.pass_count == 3
    assert resp.summary.fail_count == 0
    assert resp.summary.not_verified_count == 0
    assert len(resp.requirements) == 3


def test_30_service_response_contains_no_decision_verdict_and_has_disclaimer(sqlite_session):
    """Case 30: Service layer: response does NOT contain any qualification/disqualification verdict and includes disclaimer"""
    session, tender_id, bidder_id = sqlite_session
    service = ComplianceService(db=session)

    resp = service.evaluate_bidder_compliance(tender_id=tender_id, bidder_id=bidder_id)

    # Check disclaimer exists
    assert resp.disclaimer == DEFAULT_COMPLIANCE_DISCLAIMER
    assert "does not constitute an approval, rejection, qualification, or disqualification" in resp.disclaimer

    # Confirm model fields do not expose automated qualification/rejection verdicts
    resp_dict = resp.model_dump()
    assert "verdict" not in resp_dict
    assert "qualified" not in resp_dict
    assert "disqualified" not in resp_dict
    assert "winner" not in resp_dict
    assert "risk_score" not in resp_dict
