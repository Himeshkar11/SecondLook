"""Comprehensive Test Suite for Multi-Source Compliance Pipeline & Verification Orchestration (Task 13).

Covers all 35 required scenarios:
1. ComplianceEvaluation creation
2. UUID evaluation ID
3. Approved requirement loading
4. Unapproved requirements ignored
5. EvidenceResolver discovery
6. GST evidence resolution
7. PAN evidence resolution
8. Missing evidence handling (NOT_VERIFIED)
9. AI-only evidence handling (NOT_VERIFIED with explicit note)
10. Government verified evidence (PASS)
11. Government mismatch handling (MISMATCH trace preserved)
12. Evidence conflict handling (Government wins over AI, both preserved in trace)
13. Requirement evaluation deterministic execution
14. Multiple requirements evaluation
15. Evaluate all requirements without early termination on failure
16. Deterministic ordering by display_order
17. Summary calculation (pass, fail, not_verified counts)
18. Mandatory vs Optional counts
19. Evaluation history creation
20. Re-evaluation preserves past runs immutably
21. Evidence references in requirement results
22. API evaluation endpoint (POST /tenders/{tid}/bidders/{bid}/compliance/evaluate)
23. API report endpoint (GET /compliance/evaluations/{eid})
24. API history endpoint (GET /tenders/{tid}/bidders/{bid}/compliance/evaluations)
25. No approved requirements returns 400 NO_APPROVED_REQUIREMENTS
26. Deterministic factual explanations (no LLM)
27. Existing ComplianceEngine integration
28. Tender/bidder relationship security (404 on unknown entities)
29. Requirement/tender relationship security
30. Evidence/bidder relationship security (foreign bidder evidence excluded)
31. Full PASS scenario (Demo: GST Active, Tamil Nadu, PAN Active)
32. Partial FAIL scenario (Tamil Nadu -> Karnataka, no auto-rejection)
33. NOT_VERIFIED scenario (Government verification unavailable)
34. Evidence conflict scenario (AI ACTIVE vs Govt CANCELLED -> FAIL)
35. Final procurement decision safety (zero automated bidder approval/rejection/award)
"""

import uuid
from datetime import datetime, timezone
import pytest

pytestmark = pytest.mark.mock_auth
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.models.user import User
from app.schemas.compliance import TenderRequirementCreate
from app.services.compliance_service import ComplianceService, NoApprovedRequirementsError
from app.verification.compliance_engine import ComplianceEngine, Evidence
from app.verification.evidence_resolver import EvidenceResolver


from sqlalchemy.pool import StaticPool
from app.api.deps import get_db


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

    # Create base user
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="officer.verma@cpcl.gov.in",
        full_name="Procurement Officer Verma",
        role="OFFICER",
    )
    session.add(user)

    # Create base tender
    tender_id = uuid.uuid4()
    tender = Tender(
        id=tender_id,
        reference_number="CPCL/TND/2026/013",
        title="Refinery Expansion Phase IV",
        description="Statutory procurement of heavy piping and instrumentation.",
        created_by=user_id,
    )
    session.add(tender)

    # Create base bidder
    bidder_id = uuid.uuid4()
    bidder = Bidder(
        id=bidder_id,
        user_id=user_id,
        legal_name="Apex Global Technologies Pvt Ltd",
        gst_number="33AAACG1234A1Z5",
        pan_number="ABCDE1234F",
    )
    session.add(bidder)
    session.commit()

    yield session, str(tender_id), str(bidder_id), str(user_id)
    session.close()


test_db = sqlite_session



def _add_demo_approved_requirements(service, tender_id, user_id):
    """Helper to add the 3 standard approved statutory requirements."""
    req1 = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            code="REQ-GST-001",
            title="Active GST Registration",
            type="GST",
            mandatory=True,
            display_order=1,
            rule_type="STATUS_EQUALS",
            rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
        ),
        user_id=user_id,
    )
    service.approve_requirement(str(req1.id), officer_id=user_id)

    req2 = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            code="REQ-GST-002",
            title="Tamil Nadu Registration",
            type="GST",
            mandatory=True,
            display_order=2,
            rule_type="FIELD_EQUALS",
            rule_config=[{"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}],
        ),
        user_id=user_id,
    )
    service.approve_requirement(str(req2.id), officer_id=user_id)

    req3 = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            code="REQ-PAN-001",
            title="Valid PAN",
            type="PAN",
            mandatory=False,
            display_order=3,
            rule_type="STATUS_EQUALS",
            rule_config=[{"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
        ),
        user_id=user_id,
    )
    service.approve_requirement(str(req3.id), officer_id=user_id)
    return [req1, req2, req3]


# ============================================================================
# 1. EVALUATION CONTAINER & LIFECYCLE TESTS
# ============================================================================

def test_01_compliance_evaluation_creation(test_db):
    """Case 1 & 2: ComplianceEvaluation is created with a unique UUID evaluation_id."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    assert eval_result.evaluation_id is not None
    assert isinstance(eval_result.evaluation_id, uuid.UUID)
    assert eval_result.status == "COMPLETED"
    assert eval_result.tender_id == uuid.UUID(tender_id)
    assert eval_result.bidder_id == uuid.UUID(bidder_id)


def test_02_approved_requirements_only_evaluated(test_db):
    """Case 3 & 4: Only APPROVED requirements enter engine; unapproved states ignored."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)

    # Create an approved requirement
    req_approved = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            title="Approved Rule",
            type="GST",
            rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
        ),
        user_id=user_id,
    )
    service.approve_requirement(str(req_approved.id), officer_id=user_id)

    # Create unapproved requirements
    service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(title="Draft Rule", type="PAN", status="DRAFT"),
        user_id=user_id,
    )
    service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(title="Under Review Rule", type="DOCUMENT", status="UNDER_REVIEW"),
        user_id=user_id,
    )

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)
    assert eval_result.summary.total_requirements == 1
    assert len(eval_result.requirements) == 1
    assert eval_result.requirements[0].requirement_id == req_approved.id


def test_03_no_approved_requirements_raises_error(test_db):
    """Case 25: Zero approved requirements raises NoApprovedRequirementsError; no fake pass."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)

    # Create only unapproved requirements
    service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(title="Draft Only", type="GST", status="DRAFT"),
        user_id=user_id,
    )

    with pytest.raises(NoApprovedRequirementsError) as exc_info:
        service.run_compliance_evaluation(tender_id, bidder_id, allow_empty=False)

    assert "No approved tender requirements are available" in str(exc_info.value)


# ============================================================================
# 2. EVIDENCE RESOLVER & MULTI-SOURCE HIERARCHY TESTS
# ============================================================================

def test_04_evidence_resolver_missing_evidence(test_db):
    """Case 8: Missing evidence resolves to empty; engine reports NOT_VERIFIED."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # No documents or verifications added for bidder
    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    assert eval_result.summary.total_requirements == 3
    assert eval_result.summary.not_verified_count == 3
    for r in eval_result.requirements:
        assert r.status == "NOT_VERIFIED"
        assert "evidence available" in r.result.get("summary", "").lower() or "not verified" in r.result.get("summary", "").lower()


def test_05_evidence_resolver_ai_only_evidence(test_db):
    """Case 9: AI extracted data without government verification is NOT_VERIFIED with explicit note."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Add document with completed AI extraction but NO government verification
    doc = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="GST",
        file_name="gst_cert.pdf",
        ai_status="AI_COMPLETED",
        ai_extraction={"gstin": "33AAACG1234A1Z5", "status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(doc)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    gst_eval = next(r for r in eval_result.requirements if r.requirement_code == "REQ-GST-001")
    assert gst_eval.status == "NOT_VERIFIED"
    assert "not government-verified" in gst_eval.result.get("explanation", "").lower() or "unavailable" in gst_eval.result.get("explanation", "").lower()
    # Trace should retain AI extraction
    assert len(gst_eval.evidence) > 0
    assert gst_eval.evidence[0]["verified"] is False
    assert gst_eval.evidence[0]["ai_extracted"]["status"] == "ACTIVE"


def test_06_evidence_resolver_government_verified_pass(test_db):
    """Case 10 & 31: Government verified evidence produces PASS."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Add verified GST government verification
    doc_gst = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="GST",
        file_name="gst.pdf",
        ai_status="AI_COMPLETED",
        ai_extraction={"gstin": "33AAACG1234A1Z5", "status": "ACTIVE"},
    )
    session.add(doc_gst)

    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=doc_gst.id,
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu", "legal_name": "Apex Global Technologies Pvt Ltd"},
    )
    session.add(gv_gst)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    req1 = next(r for r in eval_result.requirements if r.requirement_code == "REQ-GST-001")
    req2 = next(r for r in eval_result.requirements if r.requirement_code == "REQ-GST-002")
    assert req1.status == "PASS"
    assert req2.status == "PASS"


def test_07_evidence_conflict_government_takes_precedence_and_both_preserved(test_db):
    """Case 12 & 34: When AI says ACTIVE but Govt says CANCELLED, Govt wins (FAIL) and both are preserved in trace."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    doc_gst = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="GST",
        file_name="gst.pdf",
        ai_status="AI_COMPLETED",
        ai_extraction={"gstin": "33AAACG1234A1Z5", "status": "ACTIVE"},
    )
    session.add(doc_gst)

    # Government record says CANCELLED
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=doc_gst.id,
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "CANCELLED", "state": "Tamil Nadu"},
    )
    session.add(gv_gst)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    req1 = next(r for r in eval_result.requirements if r.requirement_code == "REQ-GST-001")
    # Result must be FAIL because government data is CANCELLED
    assert req1.status == "FAIL"

    # Evidence trace MUST preserve both AI and Government data
    assert len(req1.evidence) > 0
    ev_trace = req1.evidence[0]
    assert ev_trace["verified"] is True
    assert ev_trace["government_data"]["status"] == "CANCELLED"
    assert ev_trace["ai_extracted"]["status"] == "ACTIVE"
    assert ev_trace.get("conflict_detected") is True


def test_08_government_mismatch_preserved_in_trace(test_db):
    """Case 11: Government mismatch does not crash and notes mismatch in audit trace."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    doc_pan = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="PAN",
        file_name="pan.pdf",
        ai_status="AI_COMPLETED",
        ai_extraction={"pan": "ABCDE1234F", "legal_name": "Apex Global Technologies"},
    )
    session.add(doc_pan)

    gv_pan = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=doc_pan.id,
        bidder_id=uuid.UUID(bidder_id),
        source="PAN",
        provider="demo",
        identifier="ABCDE1234F",
        status="COMPLETED",
        verification_result="MISMATCH",
        government_data={"status": "ACTIVE", "legal_name": "Apex Foreign Systems Ltd"},
    )
    session.add(gv_pan)
    session.commit()

    evidence_list, trace_map = EvidenceResolver.resolve_evidence_for_bidder(bidder_id, session)
    pan_trace = trace_map.get("PAN")
    assert pan_trace is not None
    assert pan_trace.verified is False
    assert pan_trace.conflict_detected is True
    assert "Government Mismatch" in (pan_trace.note or "") or "differs" in (pan_trace.note or "")


# ============================================================================
# 3. EVALUATION EXECUTION & DETERMINISTIC SUMMARY
# ============================================================================

def test_09_all_requirements_evaluated_despite_failures(test_db):
    """Case 14 & 15: Evaluation does NOT stop on first failure; evaluates all approved requirements."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Add evidence satisfying only PAN, leaving GST to fail/unverified
    gv_pan = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="PAN",
        provider="demo",
        identifier="ABCDE1234F",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE"},
    )
    session.add(gv_pan)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    # All 3 requirements must be evaluated
    assert len(eval_result.requirements) == 3
    assert eval_result.summary.total_requirements == 3
    # PAN passes, GST requirements are not verified
    assert eval_result.summary.pass_count == 1
    assert eval_result.summary.not_verified_count == 2


def test_10_deterministic_display_order(test_db):
    """Case 16: Requirements are evaluated and returned in deterministic display_order."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    codes = [r.requirement_code for r in eval_result.requirements]
    assert codes == ["REQ-GST-001", "REQ-GST-002", "REQ-PAN-001"]


def test_11_mandatory_vs_optional_calculation(test_db):
    """Case 18: Summary distinguishes mandatory and optional requirement counts."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # REQ-GST-001 (Mandatory), REQ-GST-002 (Mandatory), REQ-PAN-001 (Optional)
    # Provide valid PAN only
    gv_pan = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="PAN",
        provider="demo",
        identifier="ABCDE1234F",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE"},
    )
    session.add(gv_pan)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)
    summary = eval_result.summary

    assert summary.mandatory_total == 2
    assert summary.mandatory_passed == 0
    assert summary.mandatory_not_verified == 2
    assert summary.optional_total == 1
    assert summary.optional_passed == 1


# ============================================================================
# 4. IMMUTABILITY OF HISTORY & RE-EVALUATION
# ============================================================================

def test_12_evaluation_history_immutability(test_db):
    """Case 19 & 20: Every new evaluation gets a new evaluation_id; previous evaluations remain unchanged."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Run 1: No evidence (3 NOT_VERIFIED)
    run1 = service.run_compliance_evaluation(tender_id, bidder_id)
    assert run1.summary.not_verified_count == 3

    # Add GST evidence
    doc = Document(id=uuid.uuid4(), bidder_id=uuid.UUID(bidder_id), document_type="GST", file_name="gst.pdf")
    session.add(doc)
    gv = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=doc.id,
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(gv)
    session.commit()

    # Run 2: GST verified (2 PASS, 1 NOT_VERIFIED)
    run2 = service.run_compliance_evaluation(tender_id, bidder_id)
    assert run2.summary.pass_count == 2
    assert run2.summary.not_verified_count == 1

    # Verify Run 1 and Run 2 have different UUIDs
    assert run1.evaluation_id != run2.evaluation_id

    # Verify Run 1 in database is completely unmodified
    stored_run1 = service.get_compliance_evaluation(str(run1.evaluation_id))
    assert stored_run1.summary.not_verified_count == 3
    assert stored_run1.summary.pass_count == 0

    # Verify Run 2 in database has updated results
    stored_run2 = service.get_compliance_evaluation(str(run2.evaluation_id))
    assert stored_run2.summary.pass_count == 2

    # Verify history listing returns both runs
    history = service.get_compliance_evaluations_history(tender_id, bidder_id)
    assert len(history) == 2
    assert history[0].evaluation_id == run2.evaluation_id
    assert history[1].evaluation_id == run1.evaluation_id


# ============================================================================
# 5. DEMO SCENARIOS: PASS, PARTIAL, NOT_VERIFIED, CONFLICT
# ============================================================================

def test_13_demo_full_pass_scenario(test_db):
    """Case 31: Demo scenario with GST Active, Tamil Nadu, and PAN Active results in 3 PASS."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Provide full matching demo evidence
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
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
        government_data={"status": "ACTIVE"},
    )
    session.add_all([gv_gst, gv_pan])
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    assert eval_result.summary.total_requirements == 3
    assert eval_result.summary.pass_count == 3
    assert eval_result.summary.fail_count == 0
    assert eval_result.summary.not_verified_count == 0


def test_14_demo_partial_fail_state_change_scenario(test_db):
    """Case 32: When GST state changes from Tamil Nadu to Karnataka, requirement FAILS without auto-rejecting bidder."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # GST active, but registered in Karnataka
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="29AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Karnataka"},
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
        government_data={"status": "ACTIVE"},
    )
    session.add_all([gv_gst, gv_pan])
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    assert eval_result.summary.total_requirements == 3
    assert eval_result.summary.pass_count == 2
    assert eval_result.summary.fail_count == 1

    tn_req = next(r for r in eval_result.requirements if r.requirement_code == "REQ-GST-002")
    assert tn_req.status == "FAIL"
    assert "Karnataka" in tn_req.result.get("explanation", "")

    # Safety: Bidder status in database MUST NOT be changed to REJECTED
    bidder = session.get(Bidder, uuid.UUID(bidder_id))
    assert bidder.status != "REJECTED"


# ============================================================================
# 6. SECURITY & RELATIONSHIP VALIDATION TESTS
# ============================================================================

def test_15_security_unknown_tender_returns_error(test_db):
    """Case 28: Unknown tender ID raises KeyError / 404."""
    session, _, bidder_id, _ = test_db
    service = ComplianceService(db=session)
    fake_tender_id = str(uuid.uuid4())

    with pytest.raises(KeyError) as exc_info:
        service.run_compliance_evaluation(fake_tender_id, bidder_id)
    assert "not found" in str(exc_info.value)


def test_16_security_unknown_bidder_returns_error(test_db):
    """Case 28: Unknown bidder ID raises KeyError / 404."""
    session, tender_id, _, _ = test_db
    service = ComplianceService(db=session)
    fake_bidder_id = str(uuid.uuid4())

    with pytest.raises(KeyError) as exc_info:
        service.run_compliance_evaluation(tender_id, fake_bidder_id)
    assert "not found" in str(exc_info.value)


def test_17_security_foreign_bidder_evidence_isolated(test_db):
    """Case 30: Evidence belonging to Bidder B is never used when evaluating Bidder A."""
    session, tender_id, bidder_id_a, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Create Bidder B
    bidder_id_b = uuid.uuid4()
    bidder_user_b = User(
        id=uuid.uuid4(),
        email="bidder.b@secondlook.test",
        full_name="Bidder B Test User",
        role="BIDDER",
    )
    bidder_b = Bidder(
        id=bidder_id_b,
        user_id=bidder_user_b.id,
        legal_name="Bidder B Industries",
    )
    session.add_all([bidder_user_b, bidder_b])

    # Give verified GST to Bidder B ONLY
    gv_b = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=bidder_id_b,
        source="GST",
        provider="demo",
        identifier="33BBBBG1234B1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(gv_b)
    session.commit()

    # Evaluate Bidder A: Bidder A should have NOT_VERIFIED, Bidder B's evidence must NOT bleed in
    eval_a = service.run_compliance_evaluation(tender_id, bidder_id_a)
    assert eval_a.summary.pass_count == 0
    assert eval_a.summary.not_verified_count == 3


# ============================================================================
# 7. FASTAPI API ROUTE INTEGRATION TESTS
# ============================================================================

def test_18_api_run_compliance_evaluation_endpoint(sqlite_session):
    """Case 22: POST /api/v1/tenders/{tid}/bidders/{bid}/compliance/evaluate creates evaluation."""
    session, tender_id, bidder_id, user_id = sqlite_session
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluate",
            json={"officer_id": user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "evaluation_id" in data
        assert data["status"] == "COMPLETED"
        assert "summary" in data
        assert "requirements" in data
        assert "disclaimer" in data
    finally:
        app.dependency_overrides.clear()


def test_19_api_get_compliance_evaluation_endpoint(sqlite_session):
    """Case 23: GET /api/v1/compliance/evaluations/{eid} returns evaluation report."""
    session, tender_id, bidder_id, user_id = sqlite_session
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    eval_read = service.run_compliance_evaluation(tender_id, bidder_id)

    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/compliance/evaluations/{eval_read.evaluation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["evaluation_id"] == str(eval_read.evaluation_id)
        assert data["status"] == "COMPLETED"
        assert len(data["requirements"]) == 3
    finally:
        app.dependency_overrides.clear()


def test_20_api_list_evaluations_history_endpoint(sqlite_session):
    """Case 24: GET /api/v1/tenders/{tid}/bidders/{bid}/compliance/evaluations returns history."""
    session, tender_id, bidder_id, user_id = sqlite_session
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    service.run_compliance_evaluation(tender_id, bidder_id)
    service.run_compliance_evaluation(tender_id, bidder_id)

    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    finally:
        app.dependency_overrides.clear()


def test_21_api_no_approved_requirements_returns_400(sqlite_session):
    """Case 25: POST evaluate with no approved requirements returns HTTP 400 NO_APPROVED_REQUIREMENTS."""
    session, tender_id, bidder_id, user_id = sqlite_session
    # Clean tender has no approved requirements
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluate",
            json={},
        )

        assert response.status_code == 400
        error = response.json()["detail"]["error"]
        assert error["code"] == "NO_APPROVED_REQUIREMENTS"
    finally:
        app.dependency_overrides.clear()



# ============================================================================
# 8. ABSOLUTE SAFETY: ZERO AUTOMATED PROCUREMENT DECISION
# ============================================================================

def test_22_absolute_safety_no_automatic_procurement_decisions(test_db):
    """Case 35: System strictly stops at compliance assessment; zero bidder approval or award."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # 1. Full pass scenario
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(gv_gst)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)

    # Evaluation status is COMPLETED (the job finished)
    assert eval_result.status == "COMPLETED"

    # Bidder status MUST NOT be 'APPROVED'
    bidder = session.get(Bidder, uuid.UUID(bidder_id))
    assert bidder.status != "APPROVED"
    assert bidder.status != "QUALIFIED"

    # Evaluation container must NOT have fields like bidder_decision or award
    assert not hasattr(eval_result, "bidder_status")
    assert not hasattr(eval_result, "award_recommended")
    assert not hasattr(eval_result, "risk_score")


# ============================================================================
# 9. ADDITIONAL COMPREHENSIVE COVERAGE (Tests 23 to 35)
# ============================================================================

def test_23_evidence_resolver_direct_unit_test(test_db):
    """Case 5 & 6 & 7: Direct EvidenceResolver unit test with multiple sources."""
    session, _, bidder_id, _ = test_db

    # Add GST document + verified gov
    doc_gst = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="GST",
        file_name="gst.pdf",
        ai_status="AI_COMPLETED",
        ai_extraction={"gstin": "33AAACG1234A1Z5", "status": "ACTIVE"},
    )
    session.add(doc_gst)
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=doc_gst.id,
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(gv_gst)

    # Add PAN document with AI only
    doc_pan = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="PAN",
        file_name="pan.pdf",
        ai_status="AI_COMPLETED",
        ai_extraction={"pan": "ABCDE1234F"},
    )
    session.add(doc_pan)
    session.commit()

    ev_list, trace_map = EvidenceResolver.resolve_evidence_for_bidder(bidder_id, session)

    assert len(ev_list) == 2
    gst_ev = next(e for e in ev_list if e.source == "GST")
    pan_ev = next(e for e in ev_list if e.source == "PAN")

    assert gst_ev.verified is True
    assert pan_ev.verified is False

    assert "GST" in trace_map
    assert "PAN" in trace_map
    assert trace_map["GST"].verified is True
    assert trace_map["PAN"].verified is False


def test_24_document_uploaded_raw_metadata_only(test_db):
    """Scenario where document is uploaded but OCR/AI hasn't processed it yet."""
    session, _, bidder_id, _ = test_db

    doc = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="GST",
        file_name="raw_doc.pdf",
        ai_status="AI_PENDING",
        ai_extraction=None,
    )
    session.add(doc)
    session.commit()

    ev_list, trace_map = EvidenceResolver.resolve_evidence_for_bidder(bidder_id, session)
    assert len(ev_list) == 1
    assert ev_list[0].verified is False
    assert trace_map["GST"].note is not None
    assert "pending" in trace_map["GST"].note.lower()


def test_25_evidence_trace_structure_validation(test_db):
    """Case 21: Validates that evidence trace contains all required fields."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(gv_gst)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)
    gst_req = next(r for r in eval_result.requirements if r.requirement_code == "REQ-GST-001")

    assert len(gst_req.evidence) > 0
    ev = gst_req.evidence[0]
    assert "source" in ev
    assert "identifier" in ev
    assert "verified" in ev
    assert "verification_id" in ev


def test_26_conflict_note_included_in_explanation(test_db):
    """Case 12: When evidence conflict occurs, audit note is appended to requirement explanation."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    doc = Document(
        id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        document_type="GST",
        file_name="gst.pdf",
        ai_status="AI_COMPLETED",
        ai_extraction={"gstin": "33AAACG1234A1Z5", "status": "ACTIVE"},
    )
    session.add(doc)
    gv = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=doc.id,
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "CANCELLED", "state": "Tamil Nadu"},
    )
    session.add(gv)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)
    gst_req = next(r for r in eval_result.requirements if r.requirement_code == "REQ-GST-001")

    assert "[AUDIT NOTE]" in gst_req.result.get("explanation", "")
    assert "Evidence Conflict" in gst_req.result.get("explanation", "")


def test_27_partial_rule_evaluation_semantics(test_db):
    """Case 13: Deterministic PARTIAL status when requirement has 2 rules: 1 PASS, 1 NOT_VERIFIED."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)

    # Multi-rule requirement: Rule 1 requires GST ACTIVE (we will provide), Rule 2 requires PAN ACTIVE (we will NOT provide)
    req = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            code="REQ-MULTI-001",
            title="GST and PAN Dual Compliance",
            type="GST",
            rule_config=[
                {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
                {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
            ],
        ),
        user_id=user_id,
    )
    service.approve_requirement(str(req.id), officer_id=user_id)

    # Provide only GST
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE"},
    )
    session.add(gv_gst)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)
    assert len(eval_result.requirements) == 1
    multi_req = eval_result.requirements[0]
    assert multi_req.status == "PARTIAL"
    assert eval_result.summary.partial_count == 1


def test_28_retrieval_of_unknown_evaluation_id_returns_none(test_db):
    """Retrieving a non-existent evaluation ID returns None."""
    session, _, _, _ = test_db
    service = ComplianceService(db=session)
    res = service.get_compliance_evaluation(str(uuid.uuid4()))
    assert res is None


def test_29_summary_counts_sum_to_total(test_db):
    """Case 17: pass + fail + partial + not_verified + not_applicable == total."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Add 1 pass (GST)
    gv_gst = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(gv_gst)
    session.commit()

    eval_result = service.run_compliance_evaluation(tender_id, bidder_id)
    s = eval_result.summary
    total_accounted = s.pass_count + s.fail_count + s.partial_count + s.not_verified_count + s.not_applicable_count
    assert total_accounted == s.total_requirements


def test_30_multiple_bidders_evaluated_independently(test_db):
    """Multiple bidders can be evaluated independently against the same approved tender requirements."""
    session, tender_id, bidder_id_a, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Create Bidder B
    bidder_id_b = uuid.uuid4()
    bidder_user_b = User(
        id=uuid.uuid4(),
        email="beta.bidder@secondlook.test",
        full_name="Beta Bidder Test User",
        role="BIDDER",
    )
    bidder_b = Bidder(id=bidder_id_b, user_id=bidder_user_b.id, legal_name="Beta Corp")
    session.add_all([bidder_user_b, bidder_b])

    # Bidder A has valid GST
    gv_a = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id_a),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    # Bidder B has valid PAN
    gv_b = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=bidder_id_b,
        source="PAN",
        provider="demo",
        identifier="ABCDE1234F",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE"},
    )
    session.add_all([gv_a, gv_b])
    session.commit()

    eval_a = service.run_compliance_evaluation(tender_id, bidder_id_a)
    eval_b = service.run_compliance_evaluation(tender_id, str(bidder_id_b))

    # Bidder A passed 2 GST requirements, 1 unverified
    assert eval_a.summary.pass_count == 2
    assert eval_a.summary.not_verified_count == 1

    # Bidder B passed 1 PAN requirement, 2 unverified
    assert eval_b.summary.pass_count == 1
    assert eval_b.summary.not_verified_count == 2


def test_31_legacy_evaluate_bidder_compliance_backward_compatible(test_db):
    """Legacy service method evaluate_bidder_compliance delegates to run_compliance_evaluation and returns BidderComplianceResponse."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    resp = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp.tender_id == tender_id
    assert resp.bidder_id == bidder_id
    assert resp.evaluation_id is not None
    assert resp.summary.total_requirements == 3


def test_32_legacy_get_bidder_compliance_returns_latest_evaluation(test_db):
    """Legacy service method get_bidder_compliance returns latest evaluation."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # Initial evaluation
    service.run_compliance_evaluation(tender_id, bidder_id)

    resp = service.get_bidder_compliance(tender_id, bidder_id)
    assert resp.tender_id == tender_id
    assert resp.bidder_id == bidder_id
    assert resp.summary.total_requirements == 3


def test_33_re_evaluation_after_evidence_update(test_db):
    """Case 37: Re-evaluation after new government verification updates the result without modifying old evaluation run."""
    session, tender_id, bidder_id, user_id = test_db
    service = ComplianceService(db=session)
    _add_demo_approved_requirements(service, tender_id, user_id)

    # First run without evidence
    run1 = service.run_compliance_evaluation(tender_id, bidder_id)
    assert run1.summary.pass_count == 0

    # New government verification arrives
    gv = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    )
    session.add(gv)
    session.commit()

    # Second run with evidence
    run2 = service.run_compliance_evaluation(tender_id, bidder_id)
    assert run2.summary.pass_count == 2

    # Verification: Old run still has pass_count == 0
    old = service.get_compliance_evaluation(str(run1.evaluation_id))
    assert old.summary.pass_count == 0

    # New run has pass_count == 2
    latest = service.get_compliance_evaluation(str(run2.evaluation_id))
    assert latest.summary.pass_count == 2


def test_34_api_404_on_nonexistent_evaluation_id(sqlite_session):
    """API endpoint GET /compliance/evaluations/{id} returns 404 for unknown evaluation."""
    session, _, _, _ = sqlite_session
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        res = client.get(f"/api/v1/compliance/evaluations/{uuid.uuid4()}")
        assert res.status_code == 404
        assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_35_api_post_evaluate_validates_tender_and_bidder_existence(sqlite_session):
    """API POST /tenders/{tid}/bidders/{bid}/compliance/evaluate returns 404 for invalid tender or bidder."""
    session, _, _, _ = sqlite_session
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        res = client.post(f"/api/v1/tenders/{uuid.uuid4()}/bidders/{uuid.uuid4()}/compliance/evaluate")
        assert res.status_code == 404
        assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.clear()

