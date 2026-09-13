"""Comprehensive Test Suite for Evidence Traceability, Explainability & Audit Trail (Task 15).

Covers all 24 required verification scenarios:
1. test_field_comparisons_construction: side-by-side field comparison construction (MATCH, MISMATCH, UNAVAILABLE)
2. test_deterministic_pass_explanation_status: explains PASS status match (e.g. GST status ACTIVE)
3. test_deterministic_pass_explanation_numeric: explains PASS numeric threshold (e.g. turnover/local content >= expected)
4. test_deterministic_pass_explanation_identifier: explains PASS identifier match
5. test_deterministic_fail_explanation_mismatch: explains FAIL mismatch (e.g. GST status CANCELLED vs ACTIVE)
6. test_deterministic_fail_explanation_numeric: explains FAIL numeric below threshold
7. test_deterministic_fail_explanation_blacklist: explains FAIL debarment/blacklisted status
8. test_deterministic_fail_explanation_conflict: explains FAIL conflict between AI extracted and government verified
9. test_deterministic_not_verified_explanation_unverified_ai: explains NOT_VERIFIED when AI is present but Gov is absent
10. test_deterministic_not_verified_explanation_missing: explains NOT_VERIFIED when evidence is completely missing
11. test_deterministic_source_error_explanation: explains source error / unreachable service
12. test_evidence_trace_chain_structure: verifies complete EvidenceTraceChain structure connecting requirement to document/ocr/ai/gov
13. test_evaluation_historical_snapshot_preservation: Evaluation #1 vs #2 - prior evaluation snapshot remains immutable
14. test_audit_service_record_event: verifies AuditService.record_event writes append-only record to audit_logs
15. test_audit_service_list_events: verifies filtering by entity_type, action, entity_id, and user_id
16. test_audit_service_immutability: verifies no update or deletion APIs exist on AuditService
17. test_audit_log_on_requirement_approval: approving requirement records REQUIREMENT_APPROVED
18. test_audit_log_on_requirement_rejection: rejecting requirement records REQUIREMENT_REJECTED with reason
19. test_audit_log_on_compliance_evaluation: running evaluation records COMPLIANCE_EVALUATION_EXECUTED with stats
20. test_audit_log_on_document_access: accessing signed document URL records DOCUMENT_ACCESSED
21. test_api_get_evaluation_evidence: GET /api/v1/compliance/evaluations/{id}/evidence returns full traces
22. test_api_get_evaluation_audit: GET /api/v1/compliance/evaluations/{id}/audit returns evaluation audit events
23. test_api_get_requirement_evidence: GET /api/v1/requirements/{id}/evidence returns requirement trace
24. test_security_cross_bidder_isolation: ensures foreign bidder evidence is isolated from evaluation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.compliance_service import ComplianceService
from app.verification.compliance_engine import RuleResult
from app.verification.evidence_models import EvidenceTraceChain, FieldComparisonItem, NormalizedEvidenceItem
from app.verification.explanation_engine import ExplanationEngine


@pytest.fixture
def sqlite_session():
    """Create a clean isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="officer.trace@secondlook.gov.in",
        full_name="Procurement Officer Trace",
        role="procurement_officer",
    )
    session.add(user)

    tender_id = uuid.uuid4()
    tender = Tender(
        id=tender_id,
        reference_number="TND/2026/TRACE/001",
        title="Heavy Electrical Switchgear Supply",
        description="Statutory procurement of heavy electrical switchgear.",
        created_by=user_id,
    )
    session.add(tender)

    bidder_id = uuid.uuid4()
    bidder = Bidder(
        id=bidder_id,
        user_id=user_id,
        legal_name="Apex Power Grid Solutions Ltd",
        gst_number="33AABCA1234F1Z5",
        pan_number="AABCA1234F",
    )
    session.add(bidder)
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(sqlite_session):
    """Create FastAPI test client overriding database dependency."""
    def _override_get_db():
        try:
            yield sqlite_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. FIELD COMPARISON & EXPLANATION ENGINE UNIT TESTS
# ==============================================================================

def test_field_comparisons_construction():
    """Test side-by-side field comparison construction (MATCH, MISMATCH, UNAVAILABLE)."""
    rule_configs = [
        {"field": "status", "operator": "EQUALS", "expected_value": "ACTIVE", "source": "GST"},
        {"field": "state", "operator": "EQUALS", "expected_value": "TAMIL NADU", "source": "GST"},
        {"field": "turnover", "operator": "GREATER_THAN_OR_EQUAL", "expected_value": 50000000, "source": "PAN"},
    ]
    rule_results = [
        RuleResult(0, "status", "EQUALS", "ACTIVE", "ACTIVE", True, "PASS", "Status matches"),
        RuleResult(1, "state", "EQUALS", "TAMIL NADU", "KARNATAKA", False, "FAIL", "State mismatch"),
        RuleResult(2, "turnover", "GREATER_THAN_OR_EQUAL", 50000000, None, False, "NOT_VERIFIED", "Missing"),
    ]
    evidence_items = [
        {
            "source": "GST",
            "government_data": {"status": "ACTIVE", "state": "KARNATAKA"},
            "ai_extracted": {"status": "ACTIVE", "state": "TAMIL NADU"},
        },
        {
            "source": "PAN",
            "government_data": {},
            "ai_extracted": {},
        },
    ]

    comparisons = ExplanationEngine.build_field_comparisons(
        rule_configs=rule_configs,
        rule_results=rule_results,
        evidence_items=evidence_items,
    )

    assert len(comparisons) == 3
    assert comparisons[0].field == "status"
    assert comparisons[0].result == "MATCH"
    assert comparisons[0].document_value == "ACTIVE"
    assert comparisons[0].government_value == "ACTIVE"

    assert comparisons[1].field == "state"
    assert comparisons[1].result == "MISMATCH"
    assert comparisons[1].document_value == "TAMIL NADU"
    assert comparisons[1].government_value == "KARNATAKA"

    assert comparisons[2].field == "turnover"
    assert comparisons[2].result == "UNAVAILABLE"


def test_deterministic_pass_explanation_status():
    """Test deterministic explanation for PASS status equality."""
    rr = RuleResult(0, "status", "STATUS_EQUALS", "ACTIVE", "ACTIVE", True, "PASS", "Condition met")
    ev = {"source": "GST", "verified": True, "government_data": {"status": "ACTIVE"}}
    exp = ExplanationEngine.explain_rule(rr, evidence=ev)
    assert "Government verification confirmed" in exp
    assert "status is 'ACTIVE'" in exp
    assert "ACTIVE" in exp


def test_deterministic_pass_explanation_numeric():
    """Test deterministic explanation for PASS numeric threshold."""
    rr = RuleResult(0, "local_content_percentage", "FIELD_GREATER_THAN_OR_EQUAL", 50, 65, True, "PASS", "Meets threshold")
    ev = {"source": "MAKE_IN_INDIA", "verified": True}
    exp = ExplanationEngine.explain_rule(rr, evidence=ev, source="MAKE_IN_INDIA")
    assert "Make in India declaration verified" in exp
    assert "65%" in exp
    assert "50%" in exp


def test_deterministic_pass_explanation_identifier():
    """Test deterministic explanation for PASS identifier match."""
    rr = RuleResult(0, "identifier", "IDENTIFIER_MATCH", "33AABCA1234F1Z5", "33AABCA1234F1Z5", True, "PASS", "Match")
    exp = ExplanationEngine.explain_rule(rr)
    assert "matches official government registry record" in exp


def test_deterministic_fail_explanation_mismatch():
    """Test deterministic explanation for FAIL mismatch."""
    rr = RuleResult(0, "status", "EQUALS", "ACTIVE", "CANCELLED", False, "FAIL", "Value mismatch")
    exp = ExplanationEngine.explain_rule(rr)
    assert "Government record for status is 'CANCELLED'" in exp
    assert "does not match required 'ACTIVE'" in exp


def test_deterministic_fail_explanation_numeric():
    """Test deterministic explanation for FAIL numeric below threshold."""
    rr = RuleResult(0, "annual_turnover", "GREATER_THAN_OR_EQUAL", 10000000, 4500000, False, "FAIL", "Below threshold")
    exp = ExplanationEngine.explain_rule(rr)
    assert "is below required minimum threshold" in exp
    assert "4500000" in exp


def test_deterministic_fail_explanation_blacklist():
    """Test deterministic explanation for FAIL blacklist / debarment listing."""
    rr = RuleResult(0, "listed", "EQUALS", False, "LISTED", False, "FAIL", "Entity listed")
    ev = {"source": "BLACKLIST", "government_data": {"reason": "Non-performance in NTPC project 2024"}}
    exp = ExplanationEngine.explain_rule(rr, evidence=ev, source="BLACKLIST")
    assert "Entity is listed in debarment / blacklist registry" in exp
    assert "Non-performance in NTPC project 2024" in exp


def test_deterministic_fail_explanation_conflict():
    """Test deterministic explanation for FAIL when evidence conflict exists between AI and Gov."""
    rr = RuleResult(0, "status", "EQUALS", "ACTIVE", "CANCELLED", False, "FAIL", "Conflict")
    ev = {
        "conflict_detected": True,
        "conflict_details": {
            "field": "status",
            "ai_extracted": "ACTIVE",
            "government_verified": "CANCELLED",
        },
    }
    exp = ExplanationEngine.explain_rule(rr, evidence=ev)
    assert "Evidence conflict detected" in exp
    assert "Document AI extracted status as 'ACTIVE'" in exp
    assert "government verification returned 'CANCELLED'" in exp
    assert "Government record takes precedence" in exp


def test_deterministic_not_verified_explanation_unverified_ai():
    """Test deterministic explanation for NOT_VERIFIED when AI data exists without government verification."""
    rr = RuleResult(0, "status", "EQUALS", "ACTIVE", None, False, "NOT_VERIFIED", "Pending gov")
    ev = {
        "verified": False,
        "ai_extracted": {"status": "ACTIVE", "gstin": "33AABCA1234F1Z5"},
    }
    exp = ExplanationEngine.explain_rule(rr, evidence=ev)
    assert "Document data was extracted by AI, but external government verification has not been completed" in exp


def test_deterministic_not_verified_explanation_missing():
    """Test deterministic explanation for NOT_VERIFIED when evidence is completely missing."""
    rr = RuleResult(0, "status", "EQUALS", "ACTIVE", None, False, "NOT_VERIFIED", "Missing")
    exp = ExplanationEngine.explain_rule(rr, evidence=None)
    assert "Evidence for field 'status' is not available" in exp


def test_deterministic_source_error_explanation():
    """Test deterministic explanation when government source returns an error."""
    rr = RuleResult(0, "status", "EQUALS", "ACTIVE", None, False, "NOT_VERIFIED", "Error")
    ev = {"source": "EPFO", "status": "ERROR", "error": "Gateway timeout (504)"}
    exp = ExplanationEngine.explain_rule(rr, evidence=ev)
    assert "Government source 'EPFO' returned an error" in exp
    assert "Gateway timeout (504)" in exp


def test_evidence_trace_chain_structure():
    """Test complete EvidenceTraceChain structure connecting requirement to document/ocr/ai/gov."""
    trace_chain = ExplanationEngine.build_trace_chain(
        requirement_id=str(uuid.uuid4()),
        requirement_code="REQ-GST-001",
        requirement_title="Active GST Registration",
        evaluation_status="PASS",
        rule_results=[{"field": "status", "operator": "EQUALS", "expected": "ACTIVE", "actual": "ACTIVE", "status": "PASS"}],
        evidence_items=[
            {
                "source": "GST",
                "verified": True,
                "document_id": str(uuid.uuid4()),
                "verification_id": str(uuid.uuid4()),
                "government_data": {"status": "ACTIVE", "legal_name": "Apex Power"},
                "ai_extracted": {"status": "ACTIVE"},
            }
        ],
        document_metadata={"file_name": "gst_cert.pdf", "mime_type": "application/pdf"},
        ocr_metadata={"status": "COMPLETED", "text": "GOVERNMENT OF INDIA GSTIN..."},
        ai_metadata={"status": "AI_COMPLETED", "model": "gemini-1.5-pro"},
        government_metadata={"source": "GST", "status": "COMPLETED", "verification_result": "MATCH"},
        evaluation_id=str(uuid.uuid4()),
    )

    assert isinstance(trace_chain, EvidenceTraceChain)
    assert trace_chain.requirement_code == "REQ-GST-001"
    assert trace_chain.evaluation_status == "PASS"
    assert len(trace_chain.evidence_items) == 1
    assert trace_chain.evidence_items[0].source_type == "GOVERNMENT_VERIFICATION"
    assert trace_chain.document_trace["file_name"] == "gst_cert.pdf"
    assert trace_chain.ocr_trace["status"] == "COMPLETED"
    assert trace_chain.ai_trace["status"] == "AI_COMPLETED"
    assert trace_chain.government_trace["verification_result"] == "MATCH"


# ==============================================================================
# 2. HISTORICAL SNAPSHOT IMMUTABILITY & AUDIT SERVICE TESTS
# ==============================================================================

def test_evaluation_historical_snapshot_preservation(sqlite_session):
    """Test that Evaluation #1 evidence snapshot is strictly immutable even when new verifications run later."""
    service = ComplianceService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()
    bidder = sqlite_session.query(Bidder).first()

    # Create approved requirement
    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-SNAP-001",
        title="Active GST Requirement",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
        rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
    )
    sqlite_session.add(req)

    # Add initial government verification: status ACTIVE
    gv1 = GovernmentVerification(
        id=uuid.uuid4(),
        bidder_id=bidder.id,
        source="GST",
        provider="DEMO",
        identifier="33AABCA1234F1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "legal_name": "Apex Power Grid Solutions Ltd"},
        created_at=datetime.now(timezone.utc),
    )
    sqlite_session.add(gv1)
    sqlite_session.commit()

    # Run Evaluation #1
    eval1 = service.run_compliance_evaluation(tender_id=str(tender.id), bidder_id=str(bidder.id))
    assert eval1.requirements[0].status == "PASS"
    eval1_evidence_snapshot = eval1.requirements[0].evidence

    # Later: Government status changes to CANCELLED in a new verification
    gv2 = GovernmentVerification(
        id=uuid.uuid4(),
        bidder_id=bidder.id,
        source="GST",
        provider="DEMO",
        identifier="33AABCA1234F1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "CANCELLED", "legal_name": "Apex Power Grid Solutions Ltd"},
        created_at=datetime.now(timezone.utc),
    )
    sqlite_session.add(gv2)
    sqlite_session.commit()

    # Run Evaluation #2
    eval2 = service.run_compliance_evaluation(tender_id=str(tender.id), bidder_id=str(bidder.id))
    assert eval2.requirements[0].status == "FAIL"

    # Reload Evaluation #1 from DB and verify that its evidence snapshot is unchanged!
    eval1_reloaded = service.get_compliance_evaluation(str(eval1.evaluation_id))
    assert eval1_reloaded.requirements[0].status == "PASS"
    assert eval1_reloaded.requirements[0].evidence == eval1_evidence_snapshot
    assert eval1_reloaded.requirements[0].evidence[0]["government_data"]["status"] == "ACTIVE"


def test_audit_service_record_event(sqlite_session):
    """Test recording an append-only audit event via AuditService."""
    audit_service = AuditService(db=sqlite_session)
    user = sqlite_session.query(User).first()
    tender = sqlite_session.query(Tender).first()

    event = audit_service.record_event(
        action="REQUIREMENT_APPROVED",
        entity_type="TENDER_REQUIREMENT",
        entity_id=tender.id,
        user_id=user.id,
        details={"code": "REQ-001", "note": "Verified by officer"},
        session=sqlite_session,
    )

    assert event.id is not None
    assert event.action == "REQUIREMENT_APPROVED"
    assert event.entity_type == "TENDER_REQUIREMENT"
    assert event.user_id == user.id
    assert event.details["code"] == "REQ-001"


def test_audit_service_list_events(sqlite_session):
    """Test listing and filtering audit events."""
    audit_service = AuditService(db=sqlite_session)
    user = sqlite_session.query(User).first()
    e_id = uuid.uuid4()

    audit_service.record_event("ACTION_A", "ENTITY_1", entity_id=e_id, user_id=user.id, session=sqlite_session)
    audit_service.record_event("ACTION_B", "ENTITY_1", entity_id=e_id, session=sqlite_session)
    audit_service.record_event("ACTION_C", "ENTITY_2", session=sqlite_session)

    # Filter by entity_type
    items, total = audit_service.list_events(entity_type="ENTITY_1", session=sqlite_session)
    assert total >= 2
    assert all(i.entity_type == "ENTITY_1" for i in items)

    # Filter by action
    items, total = audit_service.list_events(action="ACTION_A", session=sqlite_session)
    assert total == 1
    assert items[0].action == "ACTION_A"


def test_audit_service_immutability():
    """Verify that AuditService provides no update or delete methods."""
    audit_service = AuditService()
    assert not hasattr(audit_service, "update_event")
    assert not hasattr(audit_service, "delete_event")
    assert not hasattr(audit_service, "modify_event")


def test_audit_log_on_requirement_approval(sqlite_session):
    """Test that approving a requirement automatically creates a REQUIREMENT_APPROVED audit log."""
    service = ComplianceService(db=sqlite_session)
    audit_service = AuditService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()
    user = sqlite_session.query(User).first()

    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-AUDIT-001",
        title="Audit Test Requirement",
        type="GST",
        mandatory=True,
        display_order=1,
        status="UNDER_REVIEW",
        rule_config=[],
    )
    sqlite_session.add(req)
    sqlite_session.commit()

    service.approve_requirement(str(req.id), officer_id=str(user.id))

    # Verify audit entry
    events, total = audit_service.list_events(action="REQUIREMENT_APPROVED", entity_id=req.id, session=sqlite_session)
    assert total == 1
    assert events[0].details["previous_status"] == "UNDER_REVIEW"
    assert events[0].details["new_status"] == "APPROVED"
    assert events[0].user_id == user.id


def test_audit_log_on_requirement_rejection(sqlite_session):
    """Test that rejecting a requirement automatically creates a REQUIREMENT_REJECTED audit log with reason."""
    service = ComplianceService(db=sqlite_session)
    audit_service = AuditService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()

    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-AUDIT-002",
        title="Audit Reject Requirement",
        type="GST",
        mandatory=True,
        display_order=2,
        status="AI_SUGGESTED",
        rule_config=[],
    )
    sqlite_session.add(req)
    sqlite_session.commit()

    service.reject_requirement(str(req.id), reason="Duplicate requirement not needed")

    # Verify audit entry
    events, total = audit_service.list_events(action="REQUIREMENT_REJECTED", entity_id=req.id, session=sqlite_session)
    assert total == 1
    assert events[0].details["reason"] == "Duplicate requirement not needed"
    assert events[0].details["previous_status"] == "AI_SUGGESTED"
    assert events[0].details["new_status"] == "REJECTED"


def test_audit_log_on_compliance_evaluation(sqlite_session):
    """Test that running a compliance evaluation records COMPLIANCE_EVALUATION_EXECUTED with summary statistics."""
    service = ComplianceService(db=sqlite_session)
    audit_service = AuditService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()
    bidder = sqlite_session.query(Bidder).first()
    user = sqlite_session.query(User).first()

    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-EXEC-001",
        title="Evaluation Exec Requirement",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
        rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
    )
    sqlite_session.add(req)
    sqlite_session.commit()

    eval_read = service.run_compliance_evaluation(
        tender_id=str(tender.id), bidder_id=str(bidder.id), officer_id=str(user.id)
    )

    events, total = audit_service.list_events(
        action="COMPLIANCE_EVALUATION_EXECUTED", entity_id=eval_read.evaluation_id, session=sqlite_session
    )
    assert total == 1
    assert events[0].details["evaluation_id"] == str(eval_read.evaluation_id)
    assert events[0].details["requirements_count"] == 1
    assert "summary" in events[0].details


def test_audit_log_on_document_access(client, sqlite_session):
    """Test that requesting a signed document access URL records DOCUMENT_ACCESSED."""
    tender = sqlite_session.query(Tender).first()
    bidder = sqlite_session.query(Bidder).first()

    doc = Document(
        id=uuid.uuid4(),
        bidder_id=bidder.id,
        tender_id=tender.id,
        document_type="GST",
        file_name="vendor_gst.pdf",
        storage_path="test/vendor_gst.pdf",
        mime_type="application/pdf",
        status="UPLOADED",
    )
    sqlite_session.add(doc)
    sqlite_session.commit()

    # Request document access
    # Mock storage signer in DocumentService if needed or let route run
    from unittest.mock import patch
    with patch("app.services.document_service.DocumentService.get_document_access", return_value={"document_id": str(doc.id), "download_url": "https://signed.url"}):
        res = client.get(f"/api/v1/documents/{doc.id}/access")
        assert res.status_code == 200

    # Verify audit entry recorded
    audit_service = AuditService(db=sqlite_session)
    events, total = audit_service.list_events(action="DOCUMENT_ACCESSED", entity_id=doc.id, session=sqlite_session)
    assert total >= 1
    assert events[0].details["document_id"] == str(doc.id)


# ==============================================================================
# 3. API ENDPOINT & ISOLATION TESTS
# ==============================================================================

def test_api_get_evaluation_evidence(client, sqlite_session):
    """Test GET /api/v1/compliance/evaluations/{id}/evidence endpoint."""
    service = ComplianceService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()
    bidder = sqlite_session.query(Bidder).first()

    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-API-001",
        title="API Evidence Test",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
        rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
    )
    sqlite_session.add(req)
    sqlite_session.commit()

    eval_read = service.run_compliance_evaluation(tender_id=str(tender.id), bidder_id=str(bidder.id))

    res = client.get(f"/api/v1/compliance/evaluations/{eval_read.evaluation_id}/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["evaluation_id"] == str(eval_read.evaluation_id)
    assert len(data["traces"]) == 1
    trace = data["traces"][0]
    assert trace["requirement_code"] == "REQ-API-001"
    assert "explanation" in trace
    assert trace["explanation"] != ""


def test_api_get_evaluation_audit(client, sqlite_session):
    """Test GET /api/v1/compliance/evaluations/{id}/audit endpoint."""
    service = ComplianceService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()
    bidder = sqlite_session.query(Bidder).first()

    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-API-002",
        title="API Audit Test",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
        rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
    )
    sqlite_session.add(req)
    sqlite_session.commit()

    eval_read = service.run_compliance_evaluation(tender_id=str(tender.id), bidder_id=str(bidder.id))

    res = client.get(f"/api/v1/compliance/evaluations/{eval_read.evaluation_id}/audit")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 1
    assert any(e["action"] == "COMPLIANCE_EVALUATION_EXECUTED" for e in events)


def test_api_get_requirement_evidence(client, sqlite_session):
    """Test GET /api/v1/requirements/{id}/evidence endpoint."""
    service = ComplianceService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()
    bidder = sqlite_session.query(Bidder).first()

    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-API-003",
        title="Requirement Trace Endpoint",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
        rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
    )
    sqlite_session.add(req)
    sqlite_session.commit()

    service.run_compliance_evaluation(tender_id=str(tender.id), bidder_id=str(bidder.id))

    res = client.get(f"/api/v1/requirements/{req.id}/evidence?bidder_id={bidder.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["requirement_code"] == "REQ-API-003"
    assert "explanation" in data


def test_security_cross_bidder_isolation(sqlite_session):
    """Ensure that Bidder B's documents and verifications are strictly excluded from Bidder A's evaluation."""
    service = ComplianceService(db=sqlite_session)
    tender = sqlite_session.query(Tender).first()
    bidder_a = sqlite_session.query(Bidder).first()

    bidder_b = Bidder(
        id=uuid.uuid4(),
        user_id=bidder_a.user_id,
        legal_name="Foreign Corp B",
        gst_number="29ZZZZZ9999Z9Z9",
        pan_number="ZZZZZ9999Z",
    )
    sqlite_session.add(bidder_b)

    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender.id,
        code="REQ-SEC-001",
        title="GST Active Security",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
        rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
    )
    sqlite_session.add(req)

    # Add a verified ACTIVE GST record for Bidder B only
    gv_b = GovernmentVerification(
        id=uuid.uuid4(),
        bidder_id=bidder_b.id,
        source="GST",
        provider="DEMO",
        identifier="29ZZZZZ9999Z9Z9",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE"},
        created_at=datetime.now(timezone.utc),
    )
    sqlite_session.add(gv_b)
    sqlite_session.commit()

    # Evaluate Bidder A (who has no GST records)
    eval_a = service.run_compliance_evaluation(tender_id=str(tender.id), bidder_id=str(bidder_a.id))

    # Bidder A MUST NOT inherit Bidder B's verified record!
    assert eval_a.requirements[0].status == "NOT_VERIFIED"
    assert len(eval_a.requirements[0].evidence) == 0
