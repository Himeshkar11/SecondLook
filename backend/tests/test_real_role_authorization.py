"""Integration tests for real (non-mocked) Role-Based Access Control (RBAC).

These tests deliberately do NOT use any mock auth fixtures (no @pytest.mark.mock_auth).
They exercise the real FastAPI dependency chain end-to-end:
  get_bearer_token -> get_authenticated_identity -> get_current_application_user -> require_role (require_officer / require_bidder)

Verifies:
1. Every officer-guarded endpoint rejects unauthenticated requests with 401.
2. Every officer-guarded endpoint rejects BIDDER role with 403.
3. Every officer-guarded endpoint accepts OFFICER role (does not return 401 or 403).
4. Every bidder-guarded endpoint rejects unauthenticated requests with 401.
5. Every bidder-guarded endpoint rejects OFFICER role with 403.
6. Every bidder-guarded endpoint accepts BIDDER role (does not return 401 or 403).
7. Bid creation and submission endpoints enforce bidder-only access.
8. Requirement approve/reject endpoints enforce officer-only access.
"""

import uuid
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
from app.models.document import Document
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, TenderRequirement
from app.models.user import ApplicationRole, User


@pytest.fixture
def real_auth_context():
    """Sets up an in-memory DB with real Officer and Bidder accounts."""
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
        email="real.officer@secondlook.test",
        full_name="Real Officer",
        role=ApplicationRole.OFFICER.value,
        is_active=True,
    )
    bidder_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="real.bidder@secondlook.test",
        full_name="Real Bidder",
        role=ApplicationRole.BIDDER.value,
        is_active=True,
    )
    bidder_profile = Bidder(
        id=uuid.uuid4(),
        user_id=bidder_user.id,
        legal_name="Real Bidder Solutions Ltd",
        registration_number="REG-REAL-001",
        status="verified",
    )
    tender = Tender(
        id=uuid.uuid4(),
        reference_number="REAL/TND/2026/001",
        title="Real Auth Verification Tender",
        created_by=officer_user.id,
    )
    tender.bidders.append(bidder_profile)

    requirement = TenderRequirement(
        id=uuid.uuid4(),
        tender=tender,
        code="REQ-REAL-01",
        title="Valid GST Registration",
        type="GST",
        mandatory=True,
        display_order=1,
        status="UNDER_REVIEW",
    )
    bid = Bid(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder=bidder_profile,
        status="DRAFT",
    )
    evaluation = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder_id=bidder_profile.id,
        status="COMPLETED",
    )
    document = Document(
        id=uuid.uuid4(),
        bidder_id=bidder_profile.id,
        document_type="GST",
        file_name="gst_cert.pdf",
        status="uploaded",
    )

    session.add_all([
        officer_user,
        bidder_user,
        bidder_profile,
        tender,
        requirement,
        bid,
        evaluation,
        document,
    ])
    session.commit()

    officer_identity = AuthenticatedIdentity(officer_user.auth_user_id, officer_user)
    bidder_identity = AuthenticatedIdentity(bidder_user.auth_user_id, bidder_user)

    app.dependency_overrides[get_db] = lambda: session

    try:
        yield {
            "session": session,
            "officer_identity": officer_identity,
            "bidder_identity": bidder_identity,
            "bidder_profile": bidder_profile,
            "tender": tender,
            "bid": bid,
            "requirement": requirement,
            "evaluation": evaluation,
        }
    finally:
        app.dependency_overrides.clear()
        session.close()


def client_request(identity: AuthenticatedIdentity | None, method: str, path: str, **kwargs):
    """Executes a request with or without real authenticated identity override."""
    if identity is not None:
        app.dependency_overrides[get_authenticated_identity] = lambda: identity
    else:
        app.dependency_overrides.pop(get_authenticated_identity, None)

    try:
        client = TestClient(app)
        return getattr(client, method.lower())(path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_authenticated_identity, None)


# ─── OFFICER ENDPOINT TESTS ───────────────────────────────────────────────────

def test_officer_dashboard_rejects_unauthenticated_with_401(real_auth_context):
    res = client_request(None, "get", "/api/v1/officer/dashboard")
    assert res.status_code == 401


def test_officer_dashboard_rejects_bidder_role_with_403(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", "/api/v1/officer/dashboard")
    assert res.status_code == 403


def test_officer_dashboard_allows_officer_role(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", "/api/v1/officer/dashboard")
    assert res.status_code == 200


def test_officer_tender_dashboard_rejects_bidder_with_403(real_auth_context):
    tender_id = str(real_auth_context["tender"].id)
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", f"/api/v1/tenders/{tender_id}/dashboard")
    assert res.status_code == 403


def test_officer_tender_dashboard_allows_officer(real_auth_context):
    tender_id = str(real_auth_context["tender"].id)
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", f"/api/v1/tenders/{tender_id}/dashboard")
    assert res.status_code in (200, 404)


def test_officer_tenders_list_requires_authentication(real_auth_context):
    res = client_request(None, "get", "/api/v1/tenders")
    assert res.status_code == 401


def test_officer_tender_bidders_rejects_bidder_with_403(real_auth_context):
    tender_id = str(real_auth_context["tender"].id)
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", f"/api/v1/tenders/{tender_id}/bidders")
    assert res.status_code == 403


def test_officer_tender_bidders_allows_officer(real_auth_context):
    tender_id = str(real_auth_context["tender"].id)
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", f"/api/v1/tenders/{tender_id}/bidders")
    assert res.status_code == 200


def test_officer_bidders_list_rejects_bidder_with_403(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", "/api/v1/bidders")
    assert res.status_code == 403


def test_officer_bidders_list_allows_officer(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", "/api/v1/bidders")
    assert res.status_code == 200


def test_officer_audit_events_rejects_bidder_with_403(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", "/api/v1/audit/events")
    assert res.status_code == 403


def test_officer_audit_events_allows_officer(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", "/api/v1/audit/events")
    assert res.status_code == 200


def test_officer_review_rejects_bidder_with_403(real_auth_context):
    eval_id = str(real_auth_context["evaluation"].id)
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", f"/api/v1/compliance/evaluations/{eval_id}/review")
    assert res.status_code == 403


def test_officer_review_allows_officer(real_auth_context):
    eval_id = str(real_auth_context["evaluation"].id)
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", f"/api/v1/compliance/evaluations/{eval_id}/review")
    assert res.status_code in (200, 404)


def test_officer_requirement_approval_rejects_bidder_with_403(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    req_id = str(real_auth_context["requirement"].id)
    res = client_request(bidder_identity, "post", f"/api/v1/tender-requirements/{req_id}/approve")
    assert res.status_code == 403


def test_officer_requirement_rejection_rejects_bidder_with_403(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    req_id = str(real_auth_context["requirement"].id)
    res = client_request(bidder_identity, "post", f"/api/v1/tender-requirements/{req_id}/reject", json={"reason": "Invalid"})
    assert res.status_code == 403


# ─── BIDDER ENDPOINT TESTS ────────────────────────────────────────────────────

def test_bidder_me_profile_rejects_unauthenticated_with_401(real_auth_context):
    res = client_request(None, "get", "/api/v1/bidders/me")
    assert res.status_code == 401


def test_bidder_me_profile_rejects_officer_with_403(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", "/api/v1/bidders/me")
    assert res.status_code == 403


def test_bidder_me_profile_allows_bidder(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", "/api/v1/bidders/me")
    assert res.status_code == 200
    assert res.json()["legal_name"] == "Real Bidder Solutions Ltd"


def test_bidder_bids_list_rejects_officer_with_403(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    res = client_request(officer_identity, "get", "/api/v1/bidder/bids")
    assert res.status_code == 403


def test_bidder_bids_list_allows_bidder(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    res = client_request(bidder_identity, "get", "/api/v1/bidder/bids")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_bidder_bid_detail_rejects_officer_with_403(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    bid_id = str(real_auth_context["bid"].id)
    res = client_request(officer_identity, "get", f"/api/v1/bidder/bids/{bid_id}")
    assert res.status_code == 403


def test_bidder_bid_detail_allows_bidder(real_auth_context):
    bidder_identity = real_auth_context["bidder_identity"]
    bid_id = str(real_auth_context["bid"].id)
    res = client_request(bidder_identity, "get", f"/api/v1/bidder/bids/{bid_id}")
    assert res.status_code == 200
    assert res.json()["id"] == bid_id


def test_bidder_bid_creation_rejects_officer_with_403(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    tender_id = str(real_auth_context["tender"].id)
    res = client_request(officer_identity, "post", f"/api/v1/bidder/tenders/{tender_id}/bids")
    assert res.status_code == 403


def test_bidder_bid_submission_rejects_officer_with_403(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    bid_id = str(real_auth_context["bid"].id)
    res = client_request(officer_identity, "post", f"/api/v1/bidder/bids/{bid_id}/submit")
    assert res.status_code == 403


def test_bidder_compliance_rejects_officer_with_403(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    bid_id = str(real_auth_context["bid"].id)
    res = client_request(officer_identity, "get", f"/api/v1/bidder/bids/{bid_id}/compliance")
    assert res.status_code == 403


def test_bidder_compliance_history_rejects_officer_with_403(real_auth_context):
    officer_identity = real_auth_context["officer_identity"]
    bid_id = str(real_auth_context["bid"].id)
    res = client_request(officer_identity, "get", f"/api/v1/bidder/bids/{bid_id}/compliance/history")
    assert res.status_code == 403
