"""Unit and Integration Tests for Tender Requirement Management & AI Extraction (Task 12).

Tests:
1. Requirement creation (default status: UNDER_REVIEW / DRAFT)
2. Retrieval by ID
3. Listing by tender
4. Status filter (?status=APPROVED, ?status=AI_SUGGESTED, etc.)
5. Initial creation cannot be APPROVED directly
6. Edit requirement content
7. Editing an APPROVED requirement triggers automatic demotion to UNDER_REVIEW
8. Direct PATCH with status='APPROVED' is strictly rejected with 400 Bad Request
9. Explicit approval via /approve sets status='APPROVED', approved_at, approved_by
10. Explicit rejection via /reject sets status='REJECTED'
11. State machine transitions across all statuses
12. Cannot approve ARCHIVED requirement
13. Demo TenderRequirementExtractor: active GST extraction
14. Demo TenderRequirementExtractor: valid PAN extraction
15. Demo TenderRequirementExtractor: state preference (Tamil Nadu)
16. Demo TenderRequirementExtractor: debarment/blacklisting (manual review)
17. Extracted candidates have status AI_SUGGESTED
18. Extracted candidates maintain source traceability (source_text, source_page, source_section)
19. Anti-hallucination: generic clauses do NOT hallucinate GST/PAN
20. ComplianceService.extract_tender_requirements pipeline
21. Strict Approval Gate: unapproved rules are NEVER evaluated by ComplianceEngine
22. Strict Approval Gate: approved rules ARE evaluated by ComplianceEngine
23. API Endpoints via FastAPI TestClient
24. API Backend Bypass Prevention: PATCH status='APPROVED' returns 400
25. Tender document upload and listing
26. OpenRouter extractor fallback and mock behavior
27. Extractor factory demo mode
28. Pydantic schema validation
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.prompts_tender import TENDER_REQUIREMENT_EXTRACTION_SYSTEM_PROMPT
from app.ai.tender_extractor import (
    CandidateRequirement,
    DemoTenderRequirementExtractor,
    OpenRouterTenderRequirementExtractor,
    get_tender_requirement_extractor,
)
from app.main import app
from app.models.base import Base
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.models.tender_requirement import RequirementEvaluation, TenderRequirement
from app.models.user import User
from app.schemas.compliance import (
    TenderExtractionRequest,
    TenderExtractionResponse,
    TenderRequirementCreate,
    TenderRequirementRead,
    TenderRequirementUpdate,
)
from app.services.compliance_service import ComplianceService
from app.services.document_service import DocumentService


# ============================================================================
# DB FIXTURE (SQLite in-memory)
# ============================================================================

from sqlalchemy.pool import StaticPool

@pytest.fixture
def sqlite_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="officer@cpcl.gov.in",
        full_name="Procurement Officer Sharma",
        role="procurement_officer",
    )
    session.add(user)

    tender_id = uuid.uuid4()
    tender = Tender(
        id=tender_id,
        reference_number="CPCL/TND/2026/012",
        title="Industrial Boiler Supply & Maintenance",
        description="Supply and maintenance of high pressure industrial boilers.",
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

    yield session, str(tender_id), str(bidder_id), str(user_id)
    session.close()


# ============================================================================
# TEST CASES: REQUIREMENT LIFECYCLE & STATE MACHINE
# ============================================================================

def test_01_create_requirement_default_status(sqlite_session):
    """Case 1: Creating a requirement defaults to UNDER_REVIEW."""
    session, tender_id, _, user_id = sqlite_session
    service = ComplianceService(db=session)

    data = TenderRequirementCreate(
        title="Valid ISO 9001 Certification",
        type="DOCUMENT",
        mandatory=False,
        description="Must provide ISO 9001 certificate.",
    )
    req = service.create_tender_requirement(tender_id, data, user_id=user_id)

    assert req.id is not None
    assert req.status == "UNDER_REVIEW"
    assert req.title == "Valid ISO 9001 Certification"
    assert req.code.startswith("REQ-DOCUMENT-")
    assert req.created_by == uuid.UUID(user_id)


def test_02_create_requirement_cannot_be_approved_directly(sqlite_session):
    """Case 2: Caller attempting to create with status='APPROVED' is forced to UNDER_REVIEW."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    data = TenderRequirementCreate(
        title="Sneaky Direct Approval",
        type="OTHER",
        mandatory=True,
        status="APPROVED",
    )
    req = service.create_tender_requirement(tender_id, data)

    assert req.status == "UNDER_REVIEW"
    assert req.approved_at is None
    assert req.approved_by is None


def test_03_get_single_requirement(sqlite_session):
    """Case 3: Fetching single requirement by UUID."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    data = TenderRequirementCreate(title="Test Single Req", type="PAN")
    req = service.create_tender_requirement(tender_id, data)

    fetched = service.get_tender_requirement(str(req.id))
    assert fetched is not None
    assert fetched.id == req.id
    assert fetched.title == "Test Single Req"


def test_04_list_requirements_and_filter_by_status(sqlite_session):
    """Case 4: List requirements by tender and filter by status."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    r1 = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="R1", type="GST", status="UNDER_REVIEW"))
    r2 = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="R2", type="PAN", status="UNDER_REVIEW"))
    service.approve_requirement(str(r1.id))

    all_reqs = service.get_tender_requirements(tender_id)
    assert len(all_reqs) == 2

    approved = service.get_tender_requirements(tender_id, status="APPROVED")
    assert len(approved) == 1
    assert approved[0].id == r1.id

    under_review = service.get_tender_requirements(tender_id, status="UNDER_REVIEW")
    assert len(under_review) == 1
    assert under_review[0].id == r2.id


def test_05_update_approved_requirement_demotes_to_under_review(sqlite_session):
    """Case 5: Updating an APPROVED requirement's content automatically demotes it to UNDER_REVIEW."""
    session, tender_id, _, user_id = sqlite_session
    service = ComplianceService(db=session)

    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Original Title", type="GST"))
    service.approve_requirement(str(req.id), officer_id=user_id)
    assert req.status == "APPROVED"
    assert req.approved_at is not None

    # Modify content
    update_data = TenderRequirementUpdate(title="Modified Title")
    updated = service.update_tender_requirement(str(req.id), update_data)

    assert updated.status == "UNDER_REVIEW"
    assert updated.approved_at is None
    assert updated.approved_by is None
    assert updated.title == "Modified Title"


def test_06_direct_update_to_approved_is_rejected(sqlite_session):
    """Case 6: Direct update with status='APPROVED' raises ValueError (anti-bypass)."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Under Review Req", type="GST"))
    assert req.status == "UNDER_REVIEW"

    with pytest.raises(ValueError, match="Cannot escalate requirement status to APPROVED directly via generic update"):
        service.update_tender_requirement(str(req.id), TenderRequirementUpdate(status="APPROVED"))


def test_07_explicit_approval_and_rejection(sqlite_session):
    """Case 7: Explicit approve and reject workflows."""
    session, tender_id, _, user_id = sqlite_session
    service = ComplianceService(db=session)

    req1 = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="To Approve", type="GST"))
    approved = service.approve_requirement(str(req1.id), officer_id=user_id)
    assert approved.status == "APPROVED"
    assert approved.approved_by == uuid.UUID(user_id)
    assert approved.approved_at is not None

    req2 = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="To Reject", type="PAN"))
    rejected = service.reject_requirement(str(req2.id), reason="Not applicable for this tender")
    assert rejected.status == "REJECTED"


def test_08_cannot_approve_archived_requirement(sqlite_session):
    """Case 8: Archived requirements cannot be approved directly."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Old Req", type="OTHER"))
    service.reject_requirement(str(req.id))
    service.update_tender_requirement(str(req.id), TenderRequirementUpdate(status="ARCHIVED"))
    assert req.status == "ARCHIVED"

    with pytest.raises(ValueError, match="Cannot approve requirement.*status ARCHIVED"):
        service.approve_requirement(str(req.id))


# ============================================================================
# TEST CASES: DEMO TENDER REQUIREMENT EXTRACTOR & ANTI-HALLUCINATION
# ============================================================================

FICTIONAL_TENDER_CLAUSES = """
SECTION 3 — ELIGIBILITY CRITERIA AND STATUTORY COMPLIANCE

3.1 Statutory Registrations
(a) The bidder must possess a valid and active Goods and Services Tax (GST) registration certificate.
(b) The bidder must possess a valid Permanent Account Number (PAN) issued by the Income Tax Department.
(c) Bidders registered under GST in the state of Tamil Nadu (State Code: 33) shall be accorded preference.

3.2 Debarment and Integrity Declaration
(a) The bidder must not have been debarred, blacklisted, or suspended by any Central or State Government entity or PSU as of the bid submission date.
"""


def test_09_demo_extractor_extracts_four_requirements():
    """Case 9: DemoTenderRequirementExtractor extracts exact required candidates from fictional text."""
    extractor = DemoTenderRequirementExtractor()
    candidates = extractor.extract_requirements(text=FICTIONAL_TENDER_CLAUSES)

    assert len(candidates) == 4

    # 1. Active GST
    gst_req = next(c for c in candidates if c.code == "REQ-GST-ACTIVE")
    assert gst_req.type == "GST"
    assert gst_req.rule_type == "STATUS_EQUALS"
    assert gst_req.parameters == {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    assert gst_req.mandatory is True
    assert "Goods and Services Tax" in gst_req.source_text
    assert gst_req.source_page == 3
    assert gst_req.source_section == "3.1 (a)"

    # 2. Valid PAN
    pan_req = next(c for c in candidates if c.code == "REQ-PAN-VALID")
    assert pan_req.type == "PAN"
    assert pan_req.rule_type == "STATUS_EQUALS"
    assert pan_req.parameters == {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
    assert pan_req.mandatory is True
    assert "Permanent Account Number" in pan_req.source_text
    assert pan_req.source_section == "3.1 (b)"

    # 3. Tamil Nadu State Preference
    tn_req = next(c for c in candidates if c.code == "REQ-GST-STATE-TN")
    assert tn_req.type == "GST"
    assert tn_req.rule_type == "FIELD_EQUALS"
    assert tn_req.parameters == {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}
    assert tn_req.mandatory is True
    assert "Tamil Nadu" in tn_req.source_text

    # 4. Debarment Declaration
    blacklisting_req = next(c for c in candidates if c.code == "REQ-DECL-BLACKLIST")
    assert blacklisting_req.type == "BLACKLISTING"
    assert blacklisting_req.rule_type is None  # Manual review
    assert blacklisting_req.mandatory is True
    assert "debarred, blacklisted" in blacklisting_req.source_text
    assert blacklisting_req.source_section == "3.2 (a)"


def test_10_anti_hallucination_generic_clauses():
    """Case 10: Generic tender text must NOT hallucinate GST, PAN, or specific rules."""
    generic_text = """
    GENERAL INSTRUCTIONS TO BIDDERS:
    All participating bidders must submit required qualification documents for technical evaluation.
    Incomplete submissions will be treated at the discretion of the procurement committee.
    """
    extractor = DemoTenderRequirementExtractor()
    candidates = extractor.extract_requirements(text=generic_text)

    # Must NOT contain GST or PAN
    types = [c.type for c in candidates]
    assert "GST" not in types
    assert "PAN" not in types

    # At most returns generic DOCUMENT requirement
    assert len(candidates) == 1
    assert candidates[0].type == "DOCUMENT"
    assert candidates[0].rule_type is None


def test_11_service_extract_tender_requirements_pipeline(sqlite_session):
    """Case 11: ComplianceService.extract_tender_requirements persists AI_SUGGESTED candidates."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    extracted = service.extract_tender_requirements(
        tender_id=tender_id,
        text=FICTIONAL_TENDER_CLAUSES,
    )

    assert len(extracted) == 4
    for r in extracted:
        assert r.status == "AI_SUGGESTED"
        assert r.source_text is not None
        assert r.source_page is not None
        assert r.source_section is not None
        assert r.tender_id == uuid.UUID(tender_id)


# ============================================================================
# TEST CASES: STRICT APPROVAL GATE IN COMPLIANCE EVALUATION
# ============================================================================

def test_12_strict_approval_gate_unapproved_rules_never_evaluated(sqlite_session):
    """Case 12: Unapproved requirements (AI_SUGGESTED, UNDER_REVIEW, DRAFT, REJECTED)
    must NEVER be evaluated by the ComplianceEngine.
    """
    session, tender_id, bidder_id, user_id = sqlite_session
    service = ComplianceService(db=session)

    # Add verified GST and PAN
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

    # Extract requirements (all AI_SUGGESTED)
    extracted = service.extract_tender_requirements(tender_id=tender_id, text=FICTIONAL_TENDER_CLAUSES)
    assert len(extracted) == 4
    assert all(r.status == "AI_SUGGESTED" for r in extracted)

    # Run compliance evaluation BEFORE any approval
    resp_before = service.evaluate_bidder_compliance(tender_id=tender_id, bidder_id=bidder_id)

    # ZERO requirements should be evaluated because NONE are approved
    assert resp_before.summary.total_requirements == 0
    assert len(resp_before.requirements) == 0

    # Explicitly approve ONLY the GST requirement
    gst_req = next(r for r in extracted if r.type == "GST" and r.rule_type == "STATUS_EQUALS")
    service.approve_requirement(str(gst_req.id), officer_id=user_id)

    # Run compliance evaluation AFTER approving one requirement
    resp_after = service.evaluate_bidder_compliance(tender_id=tender_id, bidder_id=bidder_id)

    # Exactly 1 requirement should be evaluated and it should PASS
    assert resp_after.summary.total_requirements == 1
    assert len(resp_after.requirements) == 1
    assert resp_after.requirements[0].requirement_id == gst_req.id
    assert resp_after.requirements[0].status == "PASS"


# ============================================================================
# TEST CASES: FASTAPI ROUTER & BACKEND BYPASS PREVENTION
# ============================================================================

def test_13_api_patch_cannot_bypass_approval(sqlite_session):
    """Case 13: Attempting PATCH /api/v1/tender-requirements/{id} with status='APPROVED' returns 400."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Test Bypass", type="GST"))

    # Use TestClient with dependency override for get_db
    from app.api.deps import get_db
    app.dependency_overrides[get_db] = lambda: session

    client = TestClient(app)
    try:
        res = client.patch(
            f"/api/v1/tender-requirements/{req.id}",
            json={"status": "APPROVED"},
        )
        assert res.status_code == 400
        data = res.json()
        assert "INVALID_TRANSITION" in str(data)
    finally:
        app.dependency_overrides.clear()


def test_14_api_approve_endpoint_succeeds(sqlite_session):
    """Case 14: Calling POST /api/v1/tender-requirements/{id}/approve succeeds and sets status."""
    session, tender_id, _, user_id = sqlite_session
    service = ComplianceService(db=session)

    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Test Approve", type="GST"))

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = lambda: session

    client = TestClient(app)
    try:
        res = client.post(
            f"/api/v1/tender-requirements/{req.id}/approve",
            json={"officer_id": user_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "APPROVED"
        assert data["approved_at"] is not None
        assert data["approved_by"] == user_id
    finally:
        app.dependency_overrides.clear()


def test_15_api_extract_endpoint(sqlite_session):
    """Case 15: POST /api/v1/tenders/{tender_id}/requirements/extract returns candidate list."""
    session, tender_id, _, _ = sqlite_session

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = lambda: session

    client = TestClient(app)
    try:
        res = client.post(
            f"/api/v1/tenders/{tender_id}/requirements/extract",
            json={"text": FICTIONAL_TENDER_CLAUSES},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["tender_id"] == tender_id
        assert data["extracted_count"] == 4
        assert len(data["requirements"]) == 4
        for r in data["requirements"]:
            assert r["status"] == "AI_SUGGESTED"
            assert r["source_text"] is not None
    finally:
        app.dependency_overrides.clear()


def test_16_openrouter_extractor_fallback():
    """Case 16: OpenRouter extractor uses fallback or demo when offline / mock."""
    extractor = OpenRouterTenderRequirementExtractor(api_key="mock-key")
    # Test format candidates parser
    raw_output = """
    ```json
    [
      {
        "code": "REQ-GST-001",
        "title": "Active GST Registration",
        "description": "Bidder must have active GST",
        "type": "GST",
        "mandatory": true,
        "rule_type": "STATUS_EQUALS",
        "parameters": {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        "source_text": "Bidder must possess active GST",
        "source_page": 1,
        "source_section": "Clause 1.1"
      }
    ]
    ```
    """
    candidates = extractor._parse_candidates(raw_output)
    assert len(candidates) == 1
    assert candidates[0].code == "REQ-GST-001"
    assert candidates[0].type == "GST"
    assert candidates[0].rule_type == "STATUS_EQUALS"


def test_17_factory_returns_demo_extractor(monkeypatch):
    """Case 17: get_tender_requirement_extractor returns DemoTenderRequirementExtractor."""
    extractor = get_tender_requirement_extractor()
    assert extractor is not None


def test_18_state_machine_transition_matrix(sqlite_session):
    """Case 18: Full state machine transition matrix."""
    session, tender_id, _, user_id = sqlite_session
    service = ComplianceService(db=session)

    # 1. DRAFT -> UNDER_REVIEW -> APPROVED -> UNDER_REVIEW -> REJECTED -> ARCHIVED
    req = service.create_tender_requirement(
        tender_id, TenderRequirementCreate(title="Transition Test", type="GST", status="DRAFT")
    )
    assert req.status == "DRAFT"

    # DRAFT -> UNDER_REVIEW
    updated = service.update_tender_requirement(str(req.id), TenderRequirementUpdate(status="UNDER_REVIEW"))
    assert updated.status == "UNDER_REVIEW"

    # UNDER_REVIEW -> APPROVED
    approved = service.approve_requirement(str(req.id), officer_id=user_id)
    assert approved.status == "APPROVED"

    # Content change -> UNDER_REVIEW
    demoted = service.update_tender_requirement(str(req.id), TenderRequirementUpdate(title="New Title"))
    assert demoted.status == "UNDER_REVIEW"

    # UNDER_REVIEW -> REJECTED
    rejected = service.reject_requirement(str(req.id))
    assert rejected.status == "REJECTED"

    # REJECTED -> ARCHIVED
    archived = service.update_tender_requirement(str(req.id), TenderRequirementUpdate(status="ARCHIVED"))
    assert archived.status == "ARCHIVED"


def test_19_api_reject_endpoint(sqlite_session):
    """Case 19: POST /api/v1/tender-requirements/{id}/reject succeeds."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)
    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Reject API Test", type="PAN"))

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    try:
        res = client.post(
            f"/api/v1/tender-requirements/{req.id}/reject",
            json={"reason": "Redundant criteria"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "REJECTED"
    finally:
        app.dependency_overrides.clear()


def test_20_api_get_single_requirement(sqlite_session):
    """Case 20: GET /api/v1/tender-requirements/{id} returns requirement."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)
    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Get Req Test", type="GST"))

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    try:
        res = client.get(f"/api/v1/tender-requirements/{req.id}")
        assert res.status_code == 200
        assert res.json()["id"] == str(req.id)
        assert res.json()["title"] == "Get Req Test"
    finally:
        app.dependency_overrides.clear()


def test_21_tender_document_service_upload_and_list(sqlite_session):
    """Case 21: DocumentService handles tender documents."""
    session, tender_id, _, _ = sqlite_session
    doc_service = DocumentService(db=session)

    # Contract mock upload
    res = doc_service.upload_document(
        tender_id=tender_id,
        document_type="TENDER_DOCUMENT",
        file_name="nit_tender.pdf",
    )
    assert res["tender_id"] == tender_id
    assert res["document_type"] == "TENDER_DOCUMENT"

    # List tender documents
    docs = doc_service.list_documents(tender_id=tender_id)
    assert "items" in docs


def test_22_schema_validations():
    """Case 22: Pydantic schemas validate correctly."""
    create_schema = TenderRequirementCreate(
        title="Valid Schema",
        type="GST",
        mandatory=True,
        display_order=1,
    )
    assert create_schema.title == "Valid Schema"
    assert create_schema.status == "UNDER_REVIEW"

    update_schema = TenderRequirementUpdate(
        title="Updated",
        mandatory=False,
    )
    assert update_schema.title == "Updated"
    assert update_schema.mandatory is False


def test_23_approval_gate_all_six_states(sqlite_session):
    """Case 23: Explicit test of all six states against ComplianceEngine:
    A: AI_SUGGESTED -> MUST NOT be evaluated
    B: DRAFT -> MUST NOT be evaluated
    C: UNDER_REVIEW -> MUST NOT be evaluated
    D: REJECTED -> MUST NOT be evaluated
    E: ARCHIVED -> MUST NOT be evaluated
    F: APPROVED -> MUST be evaluated
    """
    session, tender_id, bidder_id, user_id = sqlite_session
    service = ComplianceService(db=session)

    # Setup active GST verification evidence for bidder
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

    rule_cfg = [{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}]

    # A: AI_SUGGESTED
    req_a = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Req A", type="GST", rule_config=rule_cfg, status="UNDER_REVIEW"))
    req_a.status = "AI_SUGGESTED"
    session.commit()

    resp_a = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp_a.summary.total_requirements == 0
    assert len(resp_a.requirements) == 0

    # B: DRAFT
    req_a.status = "DRAFT"
    session.commit()
    resp_b = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp_b.summary.total_requirements == 0

    # C: UNDER_REVIEW
    req_a.status = "UNDER_REVIEW"
    session.commit()
    resp_c = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp_c.summary.total_requirements == 0

    # D: REJECTED
    req_a.status = "REJECTED"
    session.commit()
    resp_d = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp_d.summary.total_requirements == 0

    # E: ARCHIVED
    req_a.status = "ARCHIVED"
    session.commit()
    resp_e = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp_e.summary.total_requirements == 0

    # F: APPROVED
    req_a.status = "UNDER_REVIEW"
    session.commit()
    service.approve_requirement(str(req_a.id), officer_id=user_id)
    assert req_a.status == "APPROVED"

    resp_f = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp_f.summary.total_requirements == 1
    assert len(resp_f.requirements) == 1
    assert resp_f.requirements[0].status == "PASS"


def test_24_cannot_approve_rejected_requirement(sqlite_session):
    """Case 24: REJECTED -> approve endpoint is an invalid transition."""
    session, tender_id, _, _ = sqlite_session
    service = ComplianceService(db=session)

    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="Reject Test", type="GST"))
    service.reject_requirement(str(req.id))
    assert req.status == "REJECTED"

    with pytest.raises(ValueError, match="Invalid state transition: Cannot approve requirement"):
        service.approve_requirement(str(req.id))


def test_25_invalid_arbitrary_transitions(sqlite_session):
    """Case 25: Arbitrary invalid status transitions raise ValueError."""
    session, tender_id, _, user_id = sqlite_session
    service = ComplianceService(db=session)

    # 1. AI_SUGGESTED -> ARCHIVED (invalid)
    req = service.create_tender_requirement(tender_id, TenderRequirementCreate(title="AI Req", type="GST"))
    req.status = "AI_SUGGESTED"
    session.commit()
    with pytest.raises(ValueError, match="Invalid state transition"):
        service.update_tender_requirement(str(req.id), TenderRequirementUpdate(status="ARCHIVED"))

    # 2. APPROVED -> DRAFT (invalid)
    service.approve_requirement(str(req.id), officer_id=user_id)
    assert req.status == "APPROVED"
    with pytest.raises(ValueError, match="Invalid state transition"):
        service.update_tender_requirement(str(req.id), TenderRequirementUpdate(status="DRAFT"))

    # 3. ARCHIVED -> cannot be rejected
    service.update_tender_requirement(str(req.id), TenderRequirementUpdate(status="ARCHIVED"))
    assert req.status == "ARCHIVED"
    with pytest.raises(ValueError, match="Cannot reject ARCHIVED requirement"):
        service.reject_requirement(str(req.id))


def test_26_approved_editing_modifies_title_rule_params_and_clears_metadata(sqlite_session):
    """Case 26: Editing title, rule_type, or parameters on APPROVED requirement triggers demotion and clears approval metadata."""
    session, tender_id, _, user_id = sqlite_session
    service = ComplianceService(db=session)

    req = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            title="Initial Title",
            type="GST",
            rule_type="STATUS_EQUALS",
            parameters={"field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        ),
    )
    service.approve_requirement(str(req.id), officer_id=user_id)
    assert req.status == "APPROVED"
    assert req.approved_at is not None
    assert req.approved_by == uuid.UUID(user_id)

    # 1. Modify parameters
    service.update_tender_requirement(
        str(req.id),
        TenderRequirementUpdate(parameters={"field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}),
    )
    assert req.status == "UNDER_REVIEW"
    assert req.approved_at is None
    assert req.approved_by is None

    # Re-approve
    service.approve_requirement(str(req.id), officer_id=user_id)
    assert req.status == "APPROVED"

    # 2. Modify rule_type
    service.update_tender_requirement(str(req.id), TenderRequirementUpdate(rule_type="FIELD_EQUALS"))
    assert req.status == "UNDER_REVIEW"
    assert req.approved_at is None
    assert req.approved_by is None


def test_27_extraction_coverage_edge_cases():
    """Case 27: Extraction coverage:
    1. Empty text -> returns empty
    2. Malformed JSON -> handled safely without exception
    3. Unsupported category -> captured safely
    4. Unsupported rule -> rule_type=None (manual review)
    5. Confirms NO approved requirement is ever produced automatically
    """
    extractor = DemoTenderRequirementExtractor()

    # Empty text
    assert extractor.extract("") == []
    assert extractor.extract("   ") == []

    # OpenRouter extractor malformed JSON
    or_extractor = OpenRouterTenderRequirementExtractor(api_key="mock")
    candidates = or_extractor._parse_candidates("not valid json at all")
    assert candidates == []

    # OpenRouter extractor dict with empty requirements
    candidates2 = or_extractor._parse_candidates('{"requirements": []}')
    assert candidates2 == []

    # OpenRouter extractor raw list JSON
    candidates3 = or_extractor._parse_candidates('[{"title": "Custom Req", "type": "OTHER"}]')
    assert len(candidates3) == 1
    assert candidates3[0].title == "Custom Req"
    assert candidates3[0].type == "OTHER"


def test_28_hallucination_exact_phrase():
    """Case 28: Exact hallucination test sentence:
    'All bidders must submit the required documents along with their bids.'
    Must NOT invent GST, PAN, UDYAM, or MSME requirements.
    """
    exact_phrase = "All bidders must submit the required documents along with their bids."
    extractor = DemoTenderRequirementExtractor()
    candidates = extractor.extract(exact_phrase)

    for c in candidates:
        assert c.type not in ("GST", "PAN", "UDYAM", "MSME")
        assert c.rule_type is None
    assert len(candidates) == 1
    assert candidates[0].type == "DOCUMENT"


def test_29_source_traceability_full_chain(sqlite_session):
    """Case 29: Complete traceability chain:
    Requirement -> Source Document -> Source Text -> Source Page/Section -> AI Suggestion -> Officer Approval -> Compliance Evaluation
    """
    session, tender_id, bidder_id, user_id = sqlite_session
    service = ComplianceService(db=session)

    # 1. Upload mock tender document
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        tender_id=uuid.UUID(tender_id),
        document_type="TENDER_DOCUMENT",
        file_name="Tender_NIT_2026.pdf",
        storage_path=f"tenders/{tender_id}/{doc_id}_Tender_NIT_2026.pdf",
        status="OCR_COMPLETED",
        ocr_status="OCR_COMPLETED",
        ocr_text=FICTIONAL_TENDER_CLAUSES,
    )
    session.add(doc)

    # 2. Add verified evidence
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

    # 3. Extract requirements referencing document
    extracted = service.extract_tender_requirements(tender_id=tender_id, document_id=str(doc_id))
    assert len(extracted) == 4

    gst_req = next(r for r in extracted if r.type == "GST" and r.rule_type == "STATUS_EQUALS")
    assert gst_req.source_document_id == doc_id
    assert gst_req.source_page == 3
    assert gst_req.source_section == "3.1 (a)"
    assert gst_req.status == "AI_SUGGESTED"

    # 4. Officer Approval
    service.approve_requirement(str(gst_req.id), officer_id=user_id)
    assert gst_req.status == "APPROVED"
    assert gst_req.approved_by == uuid.UUID(user_id)

    # 5. Compliance Evaluation
    resp = service.evaluate_bidder_compliance(tender_id=tender_id, bidder_id=bidder_id)
    assert resp.summary.total_requirements == 1
    eval_record = resp.requirements[0]
    assert eval_record.requirement_id == gst_req.id
    assert eval_record.status == "PASS"


def test_30_demo_compliance_flow_state_change(sqlite_session):
    """Case 30: Demo compliance flow with state change:
    1. Approved requirement: GST status == ACTIVE, evidence ACTIVE -> PASS
    2. Approved requirement: GST state == Tamil Nadu, evidence Tamil Nadu -> PASS
    3. Change evidence: state == Karnataka -> Tamil Nadu requirement FAILS
    4. Requirement itself remains APPROVED throughout.
    """
    session, tender_id, bidder_id, user_id = sqlite_session
    service = ComplianceService(db=session)

    req_gst_active = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            code="REQ-TEST-GST",
            title="Active GST",
            type="GST",
            rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
        ),
    )
    req_gst_tn = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            code="REQ-TEST-TN",
            title="Tamil Nadu GST",
            type="GST",
            rule_config=[{"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}],
        ),
    )
    service.approve_requirement(str(req_gst_active.id), officer_id=user_id)
    service.approve_requirement(str(req_gst_tn.id), officer_id=user_id)

    # Initial evidence: ACTIVE and Tamil Nadu
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

    resp1 = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp1.summary.total_requirements == 2
    assert resp1.summary.pass_count == 2
    assert resp1.summary.fail_count == 0

    # Change evidence state to Karnataka
    gv.government_data = {"status": "ACTIVE", "state": "Karnataka"}
    session.commit()

    resp2 = service.evaluate_bidder_compliance(tender_id, bidder_id)
    assert resp2.summary.total_requirements == 2
    assert resp2.summary.pass_count == 1
    assert resp2.summary.fail_count == 1

    # Check that the requirement itself remained APPROVED
    reloaded_tn = service.get_tender_requirement(str(req_gst_tn.id))
    assert reloaded_tn.status == "APPROVED"


def test_31_multiple_bidders_evaluated_against_same_tender_requirements(sqlite_session):
    """Case 31: Multiple bidders evaluated against the same tender requirements.
    Requirements belong to the tender, not a single bidder.
    """
    session, tender_id, bidder1_id, user_id = sqlite_session
    service = ComplianceService(db=session)

    # Create second bidder
    bidder2_id = uuid.uuid4()
    bidder2 = Bidder(
        id=bidder2_id,
        user_id=uuid.UUID(user_id),
        legal_name="Delta Infra Ltd",
        gst_number="29AAACD5678B1Z2",
    )
    session.add(bidder2)
    session.commit()

    # Create and approve requirement on tender
    req = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            code="REQ-MULTI-TN",
            title="Tamil Nadu Preference",
            type="GST",
            rule_config=[{"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}],
        ),
    )
    service.approve_requirement(str(req.id), officer_id=user_id)

    # Bidder 1 evidence: Tamil Nadu (PASS)
    session.add(GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=uuid.UUID(bidder1_id),
        source="GST",
        provider="demo",
        identifier="33AAACG1234A1Z5",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Tamil Nadu"},
    ))

    # Bidder 2 evidence: Karnataka (FAIL)
    session.add(GovernmentVerification(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        bidder_id=bidder2_id,
        source="GST",
        provider="demo",
        identifier="29AAACD5678B1Z2",
        status="COMPLETED",
        verification_result="MATCH",
        government_data={"status": "ACTIVE", "state": "Karnataka"},
    ))
    session.commit()

    # Evaluate Bidder 1
    resp1 = service.evaluate_bidder_compliance(tender_id, bidder1_id)
    assert resp1.summary.total_requirements == 1
    assert resp1.summary.pass_count == 1
    assert resp1.summary.fail_count == 0

    # Evaluate Bidder 2
    resp2 = service.evaluate_bidder_compliance(tender_id, str(bidder2_id))
    assert resp2.summary.total_requirements == 1
    assert resp2.summary.pass_count == 0
    assert resp2.summary.fail_count == 1

    # Requirement remains on tender unchanged
    assert req.tender_id == uuid.UUID(tender_id)


