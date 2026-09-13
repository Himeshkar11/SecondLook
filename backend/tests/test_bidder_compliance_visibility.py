import datetime
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
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.models.user import User


@pytest.fixture
def compliance_context():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    bidder_user_a = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="bidder.alpha@secondlook.local",
        full_name="Alpha Bidder",
        role="BIDDER",
    )
    bidder_user_b = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="bidder.beta@secondlook.local",
        full_name="Beta Bidder",
        role="BIDDER",
    )
    officer_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="officer.proc@secondlook.local",
        full_name="Procurement Officer",
        role="OFFICER",
    )

    bidder_a = Bidder(
        user=bidder_user_a,
        legal_name="Alpha Tech Enterprises Ltd",
        registration_number="U72200DL2020PTC123456",
        gst_number="07AAAAA0000A1Z5",
        pan_number="AAAAA0000A",
        status="verified",
    )
    bidder_b = Bidder(
        user=bidder_user_b,
        legal_name="Beta Systems Pvt Ltd",
        registration_number="U45200MH2018PLC654321",
        gst_number="27BBBBB1111B1Z9",
        pan_number="BBBBB1111B",
        status="pending",
    )

    tender = Tender(
        id=uuid.uuid4(),
        reference_number="GEM/2026/B/881122",
        title="High Security Cloud Infrastructure",
        description="Statutory cloud services procurement.",
        status="ACTIVE",
        created_by=officer_user.id,
    )

    # Tender requirements
    req_gst = TenderRequirement(
        id=uuid.uuid4(),
        tender=tender,
        code="REQ-GST-01",
        title="Active GST Registration",
        description="Bidder must maintain an active GSTIN.",
        type="GST",
        mandatory=True,
        display_order=1,
        status="APPROVED",
    )
    req_pan = TenderRequirement(
        id=uuid.uuid4(),
        tender=tender,
        code="REQ-PAN-01",
        title="Valid Permanent Account Number",
        description="Bidder must provide a valid corporate PAN.",
        type="PAN",
        mandatory=True,
        display_order=2,
        status="APPROVED",
    )
    req_iso = TenderRequirement(
        id=uuid.uuid4(),
        tender=tender,
        code="REQ-ISO-27001",
        title="ISO 27001 Information Security",
        description="Optional information security compliance standard.",
        type="DOCUMENT",
        mandatory=False,
        display_order=3,
        status="APPROVED",
    )

    bid_a = Bid(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder=bidder_a,
        status="SUBMITTED",
        submitted_at=datetime.datetime.now(datetime.timezone.utc),
    )

    bid_b = Bid(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder=bidder_b,
        status="DRAFT",
    )

    session.add_all([
        bidder_user_a, bidder_user_b, officer_user,
        bidder_a, bidder_b, tender,
        req_gst, req_pan, req_iso,
        bid_a, bid_b
    ])
    session.commit()

    try:
        yield {
            "session": session,
            "bidder_user_a": bidder_user_a,
            "bidder_user_b": bidder_user_b,
            "officer_user": officer_user,
            "bidder_a": bidder_a,
            "bidder_b": bidder_b,
            "tender": tender,
            "req_gst": req_gst,
            "req_pan": req_pan,
            "req_iso": req_iso,
            "bid_a": bid_a,
            "bid_b": bid_b,
        }
    finally:
        app.dependency_overrides.clear()
        session.close()


def make_client(db_session, user: User | None = None) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    if user is not None:
        identity = AuthenticatedIdentity(user.auth_user_id or user.id, user)
        app.dependency_overrides[get_authenticated_identity] = lambda: identity
    else:
        app.dependency_overrides.pop(get_authenticated_identity, None)
    return TestClient(app)


def test_unauthenticated_cannot_access_compliance_endpoints(compliance_context):
    client = make_client(compliance_context["session"], user=None)
    bid_id = str(compliance_context["bid_a"].id)

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance")
    assert res.status_code == 401

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance/history")
    assert res.status_code == 401


def test_officer_cannot_call_bidder_compliance_endpoints(compliance_context):
    client = make_client(compliance_context["session"], user=compliance_context["officer_user"])
    bid_id = str(compliance_context["bid_a"].id)

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance")
    assert res.status_code == 403

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance/history")
    assert res.status_code == 403


def test_bidder_accessing_own_bid_with_no_evaluation(compliance_context):
    client = make_client(compliance_context["session"], user=compliance_context["bidder_user_a"])
    bid_id = str(compliance_context["bid_a"].id)

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "NOT_EVALUATED"
    assert data["score"] is None
    assert data["score_formatted"] == "—"
    assert data["requirements"] == []
    assert "disclaimer" in data
    assert "secondlook does not approve, qualify, rank, or award tenders" in data["disclaimer"].lower()
    assert data["message"] is not None


def test_bidder_accessing_evaluated_bid_returns_deterministic_score_and_items(compliance_context):
    session = compliance_context["session"]
    tender = compliance_context["tender"]
    bidder_a = compliance_context["bidder_a"]
    req_gst = compliance_context["req_gst"]
    req_pan = compliance_context["req_pan"]
    req_iso = compliance_context["req_iso"]

    # Create completed compliance evaluation
    now = datetime.datetime.now(datetime.timezone.utc)
    evaluation = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder_id=bidder_a.id,
        status="COMPLETED",
        summary={
            "total_requirements": 3,
            "applicable_count": 3,
            "pass_count": 2,
            "fail_count": 1,
            "partial_count": 0,
            "not_verified_count": 0,
            "not_applicable_count": 0,
            "mandatory_total": 2,
            "mandatory_passed": 2,
            "mandatory_failed": 0,
            "mandatory_not_verified": 0,
            "optional_total": 1,
            "optional_passed": 0,
            "optional_failed": 1,
            "optional_not_verified": 0,
        },
        started_at=now - datetime.timedelta(minutes=2),
        completed_at=now,
    )
    session.add(evaluation)

    # 3 requirement evaluations
    re_gst = RequirementEvaluation(
        id=uuid.uuid4(),
        evaluation_id=evaluation.id,
        requirement_id=req_gst.id,
        bidder_id=bidder_a.id,
        tender_id=tender.id,
        status="PASS",
        result={"summary": "Active GSTIN confirmed against statutory database."},
        evidence=[{"source": "GOV_API", "document_id": str(uuid.uuid4())}],
    )
    re_pan = RequirementEvaluation(
        id=uuid.uuid4(),
        evaluation_id=evaluation.id,
        requirement_id=req_pan.id,
        bidder_id=bidder_a.id,
        tender_id=tender.id,
        status="PASS",
        result={"summary": "Valid PAN confirmed with CBDT database."},
        evidence=[{"source": "CBDT_REGISTRY"}],
    )
    re_iso = RequirementEvaluation(
        id=uuid.uuid4(),
        evaluation_id=evaluation.id,
        requirement_id=req_iso.id,
        bidder_id=bidder_a.id,
        tender_id=tender.id,
        status="FAIL",
        result={"explanation": "ISO 27001 certificate expired or not provided."},
        evidence=[],
    )
    session.add_all([re_gst, re_pan, re_iso])
    session.commit()

    client = make_client(session, user=compliance_context["bidder_user_a"])
    bid_id = str(compliance_context["bid_a"].id)

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "COMPLETED"
    # 2 passed out of 3 applicable => 2/3 * 100 = 66.666... -> 66.7%
    assert data["score"] == 66.7
    assert data["score_formatted"] == "66.7%"
    assert data["summary"]["applicable_count"] == 3
    assert data["summary"]["pass_count"] == 2
    assert data["summary"]["fail_count"] == 1

    reqs = data["requirements"]
    assert len(reqs) == 3

    # Check GST requirement
    gst_item = next(r for r in reqs if r["requirement_code"] == "REQ-GST-01")
    assert gst_item["status"] == "PASS"
    assert gst_item["mandatory"] is True
    assert gst_item["has_evidence"] is True
    assert "GOV_API" in gst_item["evidence_sources"]
    assert "verified successfully" in gst_item["actionable_guidance"].lower()

    # Check ISO requirement
    iso_item = next(r for r in reqs if r["requirement_code"] == "REQ-ISO-27001")
    assert iso_item["status"] == "FAIL"
    assert iso_item["mandatory"] is False
    assert iso_item["explanation"] == "ISO 27001 certificate expired or not provided."
    assert "Review the tender requirement" in iso_item["actionable_guidance"]


def test_zero_applicable_requirements_returns_none_score(compliance_context):
    session = compliance_context["session"]
    tender = compliance_context["tender"]
    bidder_a = compliance_context["bidder_a"]

    evaluation = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder_id=bidder_a.id,
        status="COMPLETED",
        summary={
            "total_requirements": 2,
            "applicable_count": 0,
            "pass_count": 0,
            "fail_count": 0,
            "partial_count": 0,
            "not_verified_count": 0,
            "not_applicable_count": 2,
        },
    )
    session.add(evaluation)
    session.commit()

    client = make_client(session, user=compliance_context["bidder_user_a"])
    bid_id = str(compliance_context["bid_a"].id)

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance")
    assert res.status_code == 200
    data = res.json()
    assert data["score"] is None
    assert data["score_formatted"] == "—"


def test_fail_partial_not_verified_do_not_count_as_passed(compliance_context):
    session = compliance_context["session"]
    tender = compliance_context["tender"]
    bidder_a = compliance_context["bidder_a"]

    # 4 total, 1 pass, 1 fail, 1 partial, 1 not_verified => score is 1/4 = 25.0%
    evaluation = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder_id=bidder_a.id,
        status="COMPLETED",
        summary={
            "total_requirements": 4,
            "applicable_count": 4,
            "pass_count": 1,
            "fail_count": 1,
            "partial_count": 1,
            "not_verified_count": 1,
            "not_applicable_count": 0,
        },
    )
    session.add(evaluation)
    session.commit()

    client = make_client(session, user=compliance_context["bidder_user_a"])
    bid_id = str(compliance_context["bid_a"].id)

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance")
    assert res.status_code == 200
    data = res.json()
    assert data["score"] == 25.0
    assert data["score_formatted"] == "25.0%"


def test_bidder_a_cannot_view_bidder_b_compliance(compliance_context):
    client = make_client(compliance_context["session"], user=compliance_context["bidder_user_a"])
    bid_b_id = str(compliance_context["bid_b"].id)

    # Attempt to view Bidder B's bid compliance
    res = client.get(f"/api/v1/bidder/bids/{bid_b_id}/compliance")
    assert res.status_code == 403
    assert res.json()["detail"]["error"]["code"] == "FORBIDDEN"

    # Attempt to view Bidder B's compliance history
    res = client.get(f"/api/v1/bidder/bids/{bid_b_id}/compliance/history")
    assert res.status_code == 403
    assert res.json()["detail"]["error"]["code"] == "FORBIDDEN"


def test_parameter_tampering_rejected(compliance_context):
    client = make_client(compliance_context["session"], user=compliance_context["bidder_user_a"])
    bid_a_id = str(compliance_context["bid_a"].id)
    bid_b_id = str(compliance_context["bid_b"].id)

    # Injecting foreign bidder_id/user_id in query params has no effect on authorization
    res = client.get(
        f"/api/v1/bidder/bids/{bid_b_id}/compliance?bidder_id={compliance_context['bidder_a'].id}"
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"]["code"] == "FORBIDDEN"


def test_bidder_cannot_modify_compliance_results(compliance_context):
    client = make_client(compliance_context["session"], user=compliance_context["bidder_user_a"])
    bid_id = str(compliance_context["bid_a"].id)

    # Bidder cannot POST, PUT, PATCH, DELETE compliance records
    assert client.post(f"/api/v1/bidder/bids/{bid_id}/compliance", json={}).status_code in [405, 404]
    assert client.put(f"/api/v1/bidder/bids/{bid_id}/compliance", json={}).status_code in [405, 404]
    assert client.patch(f"/api/v1/bidder/bids/{bid_id}/compliance", json={}).status_code in [405, 404]
    assert client.delete(f"/api/v1/bidder/bids/{bid_id}/compliance").status_code in [405, 404]


def test_compliance_history_returns_immutable_audit_log(compliance_context):
    session = compliance_context["session"]
    tender = compliance_context["tender"]
    bidder_a = compliance_context["bidder_a"]

    now = datetime.datetime.now(datetime.timezone.utc)

    # Add 2 historical evaluations
    eval_1 = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder_id=bidder_a.id,
        status="COMPLETED",
        summary={"total_requirements": 3, "pass_count": 1, "not_applicable_count": 0},
        created_at=now - datetime.timedelta(days=2),
        completed_at=now - datetime.timedelta(days=2),
    )
    eval_2 = ComplianceEvaluation(
        id=uuid.uuid4(),
        tender_id=tender.id,
        bidder_id=bidder_a.id,
        status="COMPLETED",
        summary={"total_requirements": 3, "pass_count": 2, "not_applicable_count": 0},
        created_at=now - datetime.timedelta(days=1),
        completed_at=now - datetime.timedelta(days=1),
    )
    session.add_all([eval_1, eval_2])
    session.commit()

    client = make_client(session, user=compliance_context["bidder_user_a"])
    bid_id = str(compliance_context["bid_a"].id)

    res = client.get(f"/api/v1/bidder/bids/{bid_id}/compliance/history")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 2
    # Check that scores were computed for history runs
    # eval_2 has 2/3 = 66.7%, eval_1 has 1/3 = 33.3%
    assert any(h["score_formatted"] == "66.7%" for h in history)
    assert any(h["score_formatted"] == "33.3%" for h in history)


def test_compliance_not_found_for_unknown_bid(compliance_context):
    client = make_client(compliance_context["session"], user=compliance_context["bidder_user_a"])
    random_id = str(uuid.uuid4())

    res = client.get(f"/api/v1/bidder/bids/{random_id}/compliance")
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "BID_NOT_FOUND"
