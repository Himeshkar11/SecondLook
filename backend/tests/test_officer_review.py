"""Test Suite for Task 16 — Officer Review Layer.

Covers all 9 required verification scenarios:
1. test_review_creation: COMPLETED evaluation → create review → IN_PROGRESS
2. test_requirement_review: NOT_REVIEWED → REVIEWED
3. test_requirement_flag: NOT_REVIEWED → FLAGGED
4. test_cannot_complete_incomplete_review: missing mandatory reviews → rejected
5. test_cannot_complete_no_decision: NO_DECISION selected → rejected
6. test_successful_completion: all mandatory reviewed + valid decision → COMPLETED
7. test_processing_evaluation_rejection: evaluation = PROCESSING → completion rejected
8. test_audit_events: review lifecycle generates audit events
9. test_persistence_after_refetch: completed review survives re-fetch
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
from app.review.models import OfficerReview, RequirementReview
from app.review.service import ReviewService, ReviewValidationError
from app.services.audit_service import AuditService


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sqlite_session():
    """Clean in-memory SQLite session with all tables created."""
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
        email="officer.review@secondlook.gov.in",
        full_name="Procurement Officer",
        role="procurement_officer",
    )
    session.add(user)

    tender_id = uuid.uuid4()
    tender = Tender(
        id=tender_id,
        reference_number="TND/2026/REVIEW/001",
        title="Industrial Equipment Procurement",
        description="Test tender for officer review.",
        created_by=user_id,
    )
    session.add(tender)

    bidder_id = uuid.uuid4()
    bidder = Bidder(
        id=bidder_id,
        user_id=user_id,
        legal_name="ABC Technologies Pvt Ltd",
        gst_number="29ABCDE1234F1Z5",
        pan_number="ABCDE1234F",
    )
    session.add(bidder)
    session.commit()

    yield session, {"user_id": user_id, "tender_id": tender_id, "bidder_id": bidder_id}

    session.close()


def _make_evaluation(session, tender_id, bidder_id, status="COMPLETED", req_count=3):
    """Create a ComplianceEvaluation with N RequirementEvaluations (mandatory=True)."""
    eval_id = uuid.uuid4()
    evaluation = ComplianceEvaluation(
        id=eval_id,
        tender_id=tender_id,
        bidder_id=bidder_id,
        status=status,
        summary={
            "total": req_count,
            "passed": max(0, req_count - 2),
            "failed": 1,
            "partial": 0,
            "not_verified": 1,
            "not_applicable": 0,
        },
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc) if status == "COMPLETED" else None,
    )
    session.add(evaluation)
    session.flush()

    result_ids = []
    for i in range(req_count):
        req_id = uuid.uuid4()
        req = TenderRequirement(
            id=req_id,
            tender_id=tender_id,
            code=f"REQ-TEST-{i+1:03d}",
            title=f"Test Requirement {i+1}",
            type="GST",
            mandatory=True,
            display_order=i + 1,
            status="APPROVED",
            rule_config=[],
        )
        session.add(req)
        session.flush()

        re_id = uuid.uuid4()
        re = RequirementEvaluation(
            id=re_id,
            evaluation_id=eval_id,
            requirement_id=req_id,
            bidder_id=bidder_id,
            tender_id=tender_id,
            status="PASS" if i < (req_count - 1) else "FAIL",
            rule_results=[],
            evidence=[{"explanation": "GST status returned as ACTIVE."}],
        )
        session.add(re)
        result_ids.append(re_id)

    session.commit()
    return eval_id, result_ids


# ---------------------------------------------------------------------------
# Test 1: Review creation
# ---------------------------------------------------------------------------


def test_review_creation(sqlite_session):
    """Creating a review for a COMPLETED evaluation → status=IN_PROGRESS."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], status="COMPLETED")

    service = ReviewService(session)
    payload = service.create_review(eval_id)

    assert payload.review is not None
    assert payload.review.status == "IN_PROGRESS"
    assert payload.review.decision == "NO_DECISION"
    assert payload.evaluation_id == eval_id


# ---------------------------------------------------------------------------
# Test 2: Requirement review (NOT_REVIEWED → REVIEWED)
# ---------------------------------------------------------------------------


def test_requirement_review(sqlite_session):
    """Reviewing a requirement transitions it from NOT_REVIEWED → REVIEWED."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], status="COMPLETED")

    service = ReviewService(session)
    service.create_review(eval_id)

    rr = service.update_requirement_review(
        evaluation_id=eval_id,
        requirement_result_id=result_ids[0],
        status="REVIEWED",
        comment="Evidence confirmed by government source.",
    )

    assert rr.review_status == "REVIEWED"
    assert rr.officer_comment == "Evidence confirmed by government source."
    assert rr.reviewed_at is not None


# ---------------------------------------------------------------------------
# Test 3: Requirement flag (NOT_REVIEWED → FLAGGED)
# ---------------------------------------------------------------------------


def test_requirement_flag(sqlite_session):
    """Flagging a requirement transitions it from NOT_REVIEWED → FLAGGED."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], status="COMPLETED")

    service = ReviewService(session)
    service.create_review(eval_id)

    rr = service.update_requirement_review(
        evaluation_id=eval_id,
        requirement_result_id=result_ids[1],
        status="FLAGGED",
        comment="Needs clarification from bidder.",
    )

    assert rr.review_status == "FLAGGED"


# ---------------------------------------------------------------------------
# Test 4: Cannot complete incomplete review
# ---------------------------------------------------------------------------


def test_cannot_complete_incomplete_review(sqlite_session):
    """Completion is rejected if mandatory requirements are not reviewed."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], req_count=3)

    service = ReviewService(session)
    service.create_review(eval_id)

    # Review only 2 of 3 mandatory requirements
    service.update_requirement_review(eval_id, result_ids[0], "REVIEWED", None)
    service.update_requirement_review(eval_id, result_ids[1], "REVIEWED", None)
    service.update_decision(eval_id, "QUALIFIED", None)

    with pytest.raises(ReviewValidationError, match="mandatory requirement"):
        service.complete_review(eval_id)


# ---------------------------------------------------------------------------
# Test 5: Cannot complete without explicit decision
# ---------------------------------------------------------------------------


def test_cannot_complete_no_decision(sqlite_session):
    """Completion is rejected when decision is still NO_DECISION."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], req_count=2)

    service = ReviewService(session)
    service.create_review(eval_id)

    # Review all requirements
    for rid in result_ids:
        service.update_requirement_review(eval_id, rid, "REVIEWED", None)

    # Do NOT update decision — remains NO_DECISION
    with pytest.raises(ReviewValidationError, match="NO_DECISION"):
        service.complete_review(eval_id)


# ---------------------------------------------------------------------------
# Test 6: Successful completion
# ---------------------------------------------------------------------------


def test_successful_completion(sqlite_session):
    """Review completes when all mandatory requirements reviewed + valid decision."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], req_count=3)

    service = ReviewService(session)
    service.create_review(eval_id)

    for rid in result_ids:
        service.update_requirement_review(eval_id, rid, "REVIEWED", None)

    service.update_decision(eval_id, "REQUIRES_CLARIFICATION", "One clarification needed.")

    payload = service.complete_review(eval_id)

    assert payload.review is not None
    assert payload.review.status == "COMPLETED"
    assert payload.review.decision == "REQUIRES_CLARIFICATION"
    assert payload.review.completed_at is not None


# ---------------------------------------------------------------------------
# Test 7: PROCESSING evaluation rejected for completion
# ---------------------------------------------------------------------------


def test_processing_evaluation_rejection(sqlite_session):
    """Completion is rejected if the compliance evaluation is still PROCESSING."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(
        session, ids["tender_id"], ids["bidder_id"], status="PROCESSING", req_count=2
    )

    service = ReviewService(session)
    service.create_review(eval_id)

    for rid in result_ids:
        service.update_requirement_review(eval_id, rid, "REVIEWED", None)
    service.update_decision(eval_id, "QUALIFIED", None)

    with pytest.raises(ReviewValidationError, match="not yet COMPLETED"):
        service.complete_review(eval_id)


# ---------------------------------------------------------------------------
# Test 8: Audit events
# ---------------------------------------------------------------------------


def test_audit_events(sqlite_session):
    """Review lifecycle generates required audit events."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], req_count=2)

    service = ReviewService(session)
    service.create_review(eval_id)
    for rid in result_ids:
        service.update_requirement_review(eval_id, rid, "REVIEWED", None)
    service.update_decision(eval_id, "QUALIFIED", "All requirements satisfied.")
    service.complete_review(eval_id)

    audit_svc = AuditService(session)
    events, total = audit_svc.list_events(limit=100, session=session)
    actions = {e.action for e in events}

    assert "OFFICER_REVIEW_STARTED" in actions, "OFFICER_REVIEW_STARTED not recorded"
    assert "REQUIREMENT_REVIEWED" in actions, "REQUIREMENT_REVIEWED not recorded"
    assert "OFFICER_NOTE_ADDED" in actions, "OFFICER_NOTE_ADDED not recorded"
    assert "OFFICER_DECISION_RECORDED" in actions, "OFFICER_DECISION_RECORDED not recorded"
    assert "OFFICER_REVIEW_COMPLETED" in actions, "OFFICER_REVIEW_COMPLETED not recorded"


# ---------------------------------------------------------------------------
# Test 9: Persistence after re-fetch
# ---------------------------------------------------------------------------


def test_persistence_after_refetch(sqlite_session):
    """Completed review data survives a fresh DB query (simulates page refresh)."""
    session, ids = sqlite_session
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], req_count=2)

    service = ReviewService(session)
    service.create_review(eval_id)
    for rid in result_ids:
        service.update_requirement_review(eval_id, rid, "REVIEWED", "Confirmed.")
    service.update_decision(eval_id, "QUALIFIED", "All good.")
    service.complete_review(eval_id)

    # Re-fetch
    session.expire_all()
    payload = service.get_review_payload(eval_id)

    assert payload.review is not None
    assert payload.review.status == "COMPLETED"
    assert payload.review.decision == "QUALIFIED"
    assert payload.review.notes == "All good."
    for req_item in payload.requirements:
        assert req_item.review is not None
        assert req_item.review.review_status in {"REVIEWED", "FLAGGED"}


# ---------------------------------------------------------------------------
# HTTP API Tests via TestClient
# ---------------------------------------------------------------------------


@pytest.fixture
def client(sqlite_session):
    """FastAPI test client with SQLite session injected."""
    session, ids = sqlite_session

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as tc:
        yield tc, session, ids
    app.dependency_overrides.clear()


def test_api_get_review_not_found(client):
    """GET review for unknown evaluation returns 404."""
    tc, session, ids = client
    eval_id, _ = _make_evaluation(session, ids["tender_id"], ids["bidder_id"])

    # No review created yet — still returns payload with review=None
    resp = tc.get(f"/api/v1/compliance/evaluations/{eval_id}/review")
    assert resp.status_code == 200
    data = resp.json()
    assert data["review"] is None


def test_api_create_and_complete_review(client):
    """Full API lifecycle: create → review requirements → decision → complete."""
    tc, session, ids = client
    eval_id, result_ids = _make_evaluation(session, ids["tender_id"], ids["bidder_id"], req_count=2)

    # Create review
    resp = tc.post(f"/api/v1/compliance/evaluations/{eval_id}/review", json={})
    assert resp.status_code == 201
    assert resp.json()["review"]["status"] == "IN_PROGRESS"

    # Review each requirement
    for rid in result_ids:
        resp = tc.patch(
            f"/api/v1/compliance/evaluations/{eval_id}/review/requirements/{rid}",
            json={"status": "REVIEWED", "comment": "Verified."},
        )
        assert resp.status_code == 200
        assert resp.json()["review_status"] == "REVIEWED"

    # Set decision
    resp = tc.patch(
        f"/api/v1/compliance/evaluations/{eval_id}/review/decision",
        json={"decision": "QUALIFIED", "notes": "All requirements met."},
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "QUALIFIED"

    # Complete
    resp = tc.post(f"/api/v1/compliance/evaluations/{eval_id}/review/complete")
    assert resp.status_code == 200
    data = resp.json()
    assert data["review"]["status"] == "COMPLETED"
    assert data["review"]["decision"] == "QUALIFIED"


def test_api_invalid_decision_rejected(client):
    """PATCH /decision with invalid decision value returns 400."""
    tc, session, ids = client
    eval_id, _ = _make_evaluation(session, ids["tender_id"], ids["bidder_id"])

    tc.post(f"/api/v1/compliance/evaluations/{eval_id}/review", json={})
    resp = tc.patch(
        f"/api/v1/compliance/evaluations/{eval_id}/review/decision",
        json={"decision": "AUTO_APPROVED"},
    )
    assert resp.status_code == 400
