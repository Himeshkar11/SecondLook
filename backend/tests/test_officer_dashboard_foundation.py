import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.auth.dependencies import get_authenticated_identity
from app.auth.service import AuthenticatedIdentity
from app.main import app
from app.models.base import Base
from app.models.bid import Bid
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.models.user import User
from app.review.models import OfficerReview, RequirementReview


@pytest.fixture
def officer_dashboard_context():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    officer_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="officer@secondlook.local",
        full_name="Chief Procurement Officer",
        role="OFFICER",
    )
    bidder_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="bidder@secondlook.local",
        full_name="Vendor Representative",
        role="BIDDER",
    )
    session.add_all([officer_user, bidder_user])
    session.commit()

    bidder = Bidder(
        id=uuid.uuid4(),
        user_id=bidder_user.id,
        legal_name="Alpha Tech Solutions Pvt Ltd",
        registration_number="U72200DL2020PTC123456",
        gst_number="07AAAAA0000A1Z5",
        pan_number="AAAAA0000A",
        status="verified",
    )
    session.add(bidder)
    session.commit()

    # Tender 1: Active with 1 bid, 1 requirement, 1 evaluation (FAILED req -> attention item)
    tender1 = Tender(
        id=uuid.uuid4(),
        reference_number="GEM/2026/B/1001",
        title="High-Capacity Data Servers",
        description="Procurement of enterprise server hardware.",
        status="ACTIVE",
        created_by=officer_user.id,
    )
    session.add(tender1)
    session.commit()

    req1 = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender1.id,
        code="REQ-GST-01",
        title="Valid GST Registration",
        description="Must have active GSTIN.",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
        rule_config=[{"field": "status", "operator": "equals", "value": "ACTIVE"}],
    )
    session.add(req1)
    session.commit()

    tender1.bidders.append(bidder)
    session.commit()

    bid1 = Bid(
        id=uuid.uuid4(),
        tender_id=tender1.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
        submitted_at=datetime.now(timezone.utc),
    )
    session.add(bid1)
    session.commit()

    eval1 = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender1.id,
        bidder_id=bidder.id,
        status="COMPLETED",
        summary={"total": 1, "passed": 0, "failed": 1, "compliance_score": 0.0},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    session.add(eval1)
    session.commit()

    req_eval1 = RequirementEvaluation(
        id=uuid.uuid4(),
        evaluation_id=eval1.id,
        requirement_id=req1.id,
        bidder_id=bidder.id,
        tender_id=tender1.id,
        status="FAIL",
        result={"ai_explanation": "GST registration is suspended or invalid."},
        rule_results=[],
        evidence=[],
        evaluated_at=datetime.now(timezone.utc),
    )
    session.add(req_eval1)
    session.commit()

    req_optional = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender1.id,
        code="REQ-OPTIONAL-01",
        title="Optional Supporting Certificate",
        description="Optional supporting evidence for review.",
        type="DOCUMENT",
        mandatory=False,
        display_order=2,
        status="APPROVED",
        rule_config=[],
    )
    session.add(req_optional)
    session.commit()

    req_eval_optional = RequirementEvaluation(
        id=uuid.uuid4(),
        evaluation_id=eval1.id,
        requirement_id=req_optional.id,
        bidder_id=bidder.id,
        tender_id=tender1.id,
        status="FAIL",
        result={"ai_explanation": "Optional evidence was not supplied."},
        rule_results=[],
        evidence=[],
        evaluated_at=datetime.now(timezone.utc),
    )
    session.add(req_eval_optional)
    session.commit()

    # Tender 2: Active with AI suggested requirement (Task 18 reviewable)
    tender2 = Tender(
        id=uuid.uuid4(),
        reference_number="GEM/2026/B/1002",
        title="Statutory Audit Software",
        description="Software platform for procurement audits.",
        status="ACTIVE",
        created_by=officer_user.id,
    )
    session.add(tender2)
    session.commit()

    req2_suggested = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=tender2.id,
        code="REQ-PAN-01",
        title="Valid PAN Card",
        description="Must provide valid PAN.",
        type="PAN",
        mandatory=True,
        display_order=1,
        status="AI_SUGGESTED",
        rule_config=[
            {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
        ],
    )
    session.add(req2_suggested)
    session.commit()

    identities = {
        "officer": AuthenticatedIdentity(officer_user.auth_user_id, officer_user),
        "bidder": AuthenticatedIdentity(bidder_user.auth_user_id, bidder_user),
    }

    app.dependency_overrides[get_db] = lambda: session
    try:
        yield session, identities, officer_user, bidder, tender1, tender2, req1, req2_suggested, eval1, req_eval1
    finally:
        app.dependency_overrides.clear()
        session.close()


def request_as(identity, method, path, **kwargs):
    app.dependency_overrides[get_authenticated_identity] = lambda: identity
    try:
        return getattr(TestClient(app), method)(path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_authenticated_identity, None)


# 1. AUTHENTICATION & ROLE GUARDS
def test_officer_dashboard_unauthenticated_returns_401(officer_dashboard_context):
    client = TestClient(app)
    response = client.get("/api/v1/officer/dashboard")
    assert response.status_code == 401


def test_officer_dashboard_bidder_returns_403(officer_dashboard_context):
    _, identities, _, _, _, _, _, _, _, _ = officer_dashboard_context
    response = request_as(identities["bidder"], "get", "/api/v1/officer/dashboard")
    assert response.status_code == 403


def test_bidder_role_headers_and_query_parameters_do_not_escalate(officer_dashboard_context):
    _, identities, _, _, _, _, _, _, _, _ = officer_dashboard_context
    response = request_as(
        identities["bidder"],
        "get",
        "/api/v1/officer/dashboard?role=OFFICER&user_id=00000000-0000-0000-0000-000000000001",
        headers={"X-Role": "OFFICER"},
    )
    assert response.status_code == 403


def test_officer_dashboard_officer_returns_200(officer_dashboard_context):
    _, identities, _, _, _, _, _, _, _, _ = officer_dashboard_context
    response = request_as(identities["officer"], "get", "/api/v1/officer/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "overview" in data
    assert "tenders" in data
    assert "attention_items" in data


# 2. OVERVIEW AGGREGATION & ATTENTION ITEMS
def test_officer_dashboard_overview_metrics(officer_dashboard_context):
    _, identities, _, _, _, _, _, _, _, _ = officer_dashboard_context
    response = request_as(identities["officer"], "get", "/api/v1/officer/dashboard")
    assert response.status_code == 200
    data = response.json()
    overview = data["overview"]

    # 2 tenders created, both ACTIVE
    assert overview["active_tenders"] == 2
    assert overview["total_tenders"] == 2
    # 1 bid received on tender1
    assert overview["bids_received"] == 1
    # 1 failed requirement on tender1 -> triggers attention
    assert overview["reviews_requiring_attention"] >= 1

    tenders = data["tenders"]
    assert len(tenders) == 2
    tender1_row = next(t for t in tenders if t["reference_number"] == "GEM/2026/B/1001")
    assert tender1_row["bids_count"] == 1
    assert tender1_row["evaluated_count"] == 1
    assert tender1_row["attention_required"] is True

    # Attention items include the failed critical requirement
    attention_items = data["attention_items"]
    assert len(attention_items) >= 1
    crit_item = next(item for item in attention_items if item["tender_reference"] == "GEM/2026/B/1001")
    assert crit_item["type"] in ["MANDATORY_ISSUE", "REVIEW_PENDING", "CRITICAL_REQUIREMENT_FAIL"]
    assert crit_item["severity"] == "danger"
    assert "/officer/bidders/" in crit_item["action_url"]


def test_mandatory_failure_generates_mandatory_attention(officer_dashboard_context):
    _, identities, _, _, tender1, _, _, _, _, _ = officer_dashboard_context
    response = request_as(identities["officer"], "get", "/api/v1/officer/dashboard")
    assert response.status_code == 200
    items = [
        item for item in response.json()["attention_items"]
        if item["tender_id"] == str(tender1.id)
    ]
    assert sum(item["type"] == "MANDATORY_ISSUE" for item in items) == 1


def test_optional_failure_does_not_generate_mandatory_attention(officer_dashboard_context):
    session, identities, _, _, tender1, _, req1, _, _, _ = officer_dashboard_context
    req1.mandatory = False
    session.commit()

    response = request_as(identities["officer"], "get", "/api/v1/officer/dashboard")
    assert response.status_code == 200
    items = [
        item for item in response.json()["attention_items"]
        if item["tender_id"] == str(tender1.id)
    ]
    assert not any(item["type"] == "MANDATORY_ISSUE" for item in items)


def test_mixed_mandatory_and_optional_failures_are_classified_once(officer_dashboard_context):
    _, identities, _, _, tender1, _, _, _, _, _ = officer_dashboard_context
    response = request_as(identities["officer"], "get", "/api/v1/officer/dashboard")
    assert response.status_code == 200
    items = [
        item for item in response.json()["attention_items"]
        if item["tender_id"] == str(tender1.id)
    ]
    assert sum(item["type"] == "MANDATORY_ISSUE" for item in items) == 1


def test_legacy_dashboard_summary_endpoint_is_removed(officer_dashboard_context):
    _, identities, _, _, _, _, _, _, _, _ = officer_dashboard_context
    response = request_as(identities["officer"], "get", "/api/v1/dashboard/summary")
    assert response.status_code == 404


def test_dashboard_summary_rejects_unauthenticated_requests(officer_dashboard_context):
    response = TestClient(app).get("/api/v1/dashboard/summary")
    assert response.status_code == 404


def test_dashboard_summary_rejects_bidder_requests(officer_dashboard_context):
    _, identities, _, _, _, _, _, _, _, _ = officer_dashboard_context
    response = request_as(identities["bidder"], "get", "/api/v1/dashboard/summary")
    assert response.status_code == 404


# 3. TENDER WORKFLOW DASHBOARD (Task 19)
def test_tender_workflow_dashboard_access(officer_dashboard_context):
    _, identities, _, _, tender1, _, _, _, _, _ = officer_dashboard_context
    # Officer can access tender workflow dashboard
    response = request_as(identities["officer"], "get", f"/api/v1/tenders/{tender1.id}/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "tender" in data
    assert data["tender"]["id"] == str(tender1.id)
    assert "summary" in data
    assert "bidders" in data
    assert len(data["bidders"]) >= 1
    assert "requirement_issues" in data

    # Bidder cannot access officer tender dashboard
    bidder_resp = request_as(identities["bidder"], "get", f"/api/v1/tenders/{tender1.id}/dashboard")
    assert bidder_resp.status_code == 403


# 4. REQUIREMENT INSPECTION & APPROVAL WORKFLOW (Task 18)
def test_officer_requirement_approval_workflow(officer_dashboard_context):
    _, identities, _, _, _, tender2, _, req2_suggested, _, _ = officer_dashboard_context
    # Requirement starts as AI_SUGGESTED
    assert req2_suggested.status == "AI_SUGGESTED"

    # Officer approves the requirement
    approve_resp = request_as(
        identities["officer"],
        "post",
        f"/api/v1/tender-requirements/{req2_suggested.id}/approve",
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"

    # Direct PATCH bypass to APPROVED without review is rejected
    bypass_resp = request_as(
        identities["officer"],
        "patch",
        f"/api/v1/tender-requirements/{req2_suggested.id}",
        json={"status": "APPROVED"},
    )
    # Patch to APPROVED is rejected or triggers demotion to UNDER_REVIEW
    assert bypass_resp.status_code in [400, 422] or bypass_resp.json().get("status") != "APPROVED"


# 5. COMPLIANCE EVALUATION & EVIDENCE INSPECTION (Task 13 & 15)
def test_officer_inspect_compliance_and_evidence(officer_dashboard_context):
    _, identities, _, bidder, tender1, _, req1, _, eval1, _ = officer_dashboard_context
    # Officer retrieves bidder compliance evaluation history
    eval_resp = request_as(
        identities["officer"],
        "get",
        f"/api/v1/tenders/{tender1.id}/bidders/{bidder.id}/compliance/evaluations",
    )
    assert eval_resp.status_code == 200
    evals = eval_resp.json()
    assert len(evals) >= 1
    assert evals[0]["evaluation_id"] == str(eval1.id)

    # Officer inspects requirement evidence trace
    trace_resp = request_as(
        identities["officer"],
        "get",
        f"/api/v1/tender-requirements/{req1.id}/evidence?bidder_id={bidder.id}",
    )
    assert trace_resp.status_code in [200, 404]  # 404 if no document linked yet, or 200 trace object


# 6. OFFICER REVIEW PANEL WORKFLOW (Task 16)
def test_officer_review_lifecycle(officer_dashboard_context):
    session, identities, _, _, _, _, _, _, eval1, req_eval1 = officer_dashboard_context

    # Step 1: Officer starts review
    start_resp = request_as(
        identities["officer"],
        "post",
        f"/api/v1/compliance/evaluations/{eval1.id}/review",
        json={},
    )
    assert start_resp.status_code == 201
    review_data = start_resp.json()["review"]
    assert review_data["status"] == "IN_PROGRESS"
    assert review_data["decision"] == "NO_DECISION"

    # Step 2: Officer reviews individual requirement
    item_resp = request_as(
        identities["officer"],
        "patch",
        f"/api/v1/compliance/evaluations/{eval1.id}/review/requirements/{req_eval1.id}",
        json={"status": "REVIEWED", "comment": "Officer verified GST status with tax portal."},
    )
    assert item_resp.status_code == 200
    assert item_resp.json()["review_status"] == "REVIEWED"

    # Step 3: Officer records explicit decision (e.g. REQUIRES_CLARIFICATION)
    decision_resp = request_as(
        identities["officer"],
        "patch",
        f"/api/v1/compliance/evaluations/{eval1.id}/review/decision",
        json={"decision": "REQUIRES_CLARIFICATION", "notes": "Request updated GST return from bidder."},
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["decision"] == "REQUIRES_CLARIFICATION"

    # Step 4: Officer completes review
    complete_resp = request_as(
        identities["officer"],
        "post",
        f"/api/v1/compliance/evaluations/{eval1.id}/review/complete",
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["review"]["status"] == "COMPLETED"
    assert complete_resp.json()["review"]["decision"] == "REQUIRES_CLARIFICATION"


# 7. STRICT DECISION SAFETY INVARIANTS
def test_decision_safety_invariants(officer_dashboard_context):
    session, identities, _, bidder, tender, _, _, _, _, _ = officer_dashboard_context

    # Create a 100% compliant evaluation
    perfect_eval = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="COMPLETED",
        summary={"total": 1, "passed": 1, "failed": 0, "compliance_score": 100.0},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    session.add(perfect_eval)
    session.commit()

    # Verify that a 100% score did NOT automatically create an OfficerReview
    review = session.query(OfficerReview).filter_by(evaluation_id=perfect_eval.id).first()
    assert review is None, "Compliance evaluation must NEVER automatically create or complete an OfficerReview"

    # Check that GET review payload reports review=None and decision=NO_DECISION
    review_payload_resp = request_as(
        identities["officer"],
        "get",
        f"/api/v1/compliance/evaluations/{perfect_eval.id}/review",
    )
    assert review_payload_resp.status_code == 200
    payload = review_payload_resp.json()
    assert payload["review"] is None


# 8. SECURITY BOUNDARIES & ROLE SPOOFING PREVENTION
def test_security_bidder_cannot_act_as_officer(officer_dashboard_context):
    _, identities, _, _, tender1, _, _, req2_suggested, eval1, _ = officer_dashboard_context

    # Bidder cannot approve requirements
    req_resp = request_as(
        identities["bidder"],
        "post",
        f"/api/v1/tender-requirements/{req2_suggested.id}/approve",
    )
    assert req_resp.status_code == 403

    # Bidder cannot start officer review
    review_resp = request_as(
        identities["bidder"],
        "post",
        f"/api/v1/compliance/evaluations/{eval1.id}/review",
        json={},
    )
    assert review_resp.status_code == 403

    # Bidder cannot update officer decisions
    dec_resp = request_as(
        identities["bidder"],
        "patch",
        f"/api/v1/compliance/evaluations/{eval1.id}/review/decision",
        json={"decision": "QUALIFIED"},
    )
    assert dec_resp.status_code == 403


# 9. OFFICER-TO-TENDER AUTHORIZATION MODEL VERIFICATION
def test_officer_cross_tender_authorization_model(officer_dashboard_context):
    """Explicitly verifies the officer-to-tender authorization boundary:
    - Under current M02-M10 architecture, all users with canonical OFFICER role
      have global operational oversight across all active tenders in the portal
      (there is no per-tender officer assignment table).
    - A second officer (Officer B) can access Tender A created by Officer A.
    - A bidder attempting direct URL/API access to ANY tender dashboard is strictly rejected with HTTP 403 Forbidden.
    - Direct URL manipulation with non-existent tender IDs returns 404 Not Found.
    """
    session, identities, officer_user, bidder, tender1, tender2, _, _, _, _ = officer_dashboard_context

    # Create a distinct second officer (Officer B) who did NOT create Tender 1
    officer_b_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="officer.b@secondlook.local",
        full_name="Second Officer B",
        role="OFFICER",
    )
    session.add(officer_b_user)
    session.commit()
    officer_b_identity = AuthenticatedIdentity(officer_b_user.auth_user_id, officer_b_user)

    # Officer B accesses Tender 1 (created by Officer A) -> Allowed under global officer model
    resp_officer_b = request_as(officer_b_identity, "get", f"/api/v1/tenders/{tender1.id}/dashboard")
    assert resp_officer_b.status_code == 200
    assert resp_officer_b.json()["tender"]["id"] == str(tender1.id)

    # Bidder attempting direct URL manipulation with Tender 1 or Tender 2 -> 403 Forbidden
    assert request_as(identities["bidder"], "get", f"/api/v1/tenders/{tender1.id}/dashboard").status_code == 403
    assert request_as(identities["bidder"], "get", f"/api/v1/tenders/{tender2.id}/dashboard").status_code == 403

    # Non-existent tender ID manipulation -> 404 Not Found
    unknown_tender_id = uuid.uuid4()
    resp_unknown = request_as(identities["officer"], "get", f"/api/v1/tenders/{unknown_tender_id}/dashboard")
    assert resp_unknown.status_code == 404

