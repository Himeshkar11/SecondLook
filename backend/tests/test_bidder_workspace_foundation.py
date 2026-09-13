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
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.tender import Tender
from app.models.user import User


@pytest.fixture
def bidder_workspace_context():
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
        email="bidder.a@secondlook.local",
        full_name="Alice Bidder",
        role="BIDDER",
    )
    bidder_user_b = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="bidder.b@secondlook.local",
        full_name="Bob Bidder",
        role="BIDDER",
    )
    bidder_user_c = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="bidder.c@secondlook.local",
        full_name="Carol Bidder",
        role="BIDDER",
    )
    officer_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="officer@secondlook.local",
        full_name="Charlie Officer",
        role="OFFICER",
    )

    bidder_a = Bidder(
        user=bidder_user_a,
        legal_name="Alpha Technologies Pvt Ltd",
        registration_number="U72200DL2020PTC123456",
        gst_number="07AAAAA0000A1Z5",
        pan_number="AAAAA0000A",
        status="verified",
    )
    bidder_b = Bidder(
        user=bidder_user_b,
        legal_name="Beta Infrastructure Ltd",
        registration_number="U45200MH2018PLC654321",
        gst_number="27BBBBB1111B1Z9",
        pan_number="BBBBB1111B",
        status="pending",
    )
    bidder_c = Bidder(
        user=bidder_user_c,
        legal_name="Gamma Services Ltd",
        status="pending",
    )

    tender = Tender(
        id=uuid.uuid4(),
        reference_number="GEM/2026/B/778899",
        title="Procurement of Statutory Compliance Monitoring Tools",
        description="Statutory monitoring software for public procurement.",
        status="ACTIVE",
        created_by=officer_user.id,
    )
    tender.bidders.append(bidder_a)

    doc_a = Document(
        bidder=bidder_a,
        document_type="GST",
        file_name="alpha-gst.pdf",
        status="verified",
    )
    doc_b = Document(
        bidder=bidder_b,
        document_type="PAN",
        file_name="beta-pan.pdf",
        status="uploaded",
    )

    session.add_all([
        bidder_user_a,
        bidder_user_b,
        bidder_user_c,
        officer_user,
        bidder_a,
        bidder_b,
        bidder_c,
        tender,
        doc_a,
        doc_b,
    ])
    session.commit()

    identities = {
        "bidder_a": AuthenticatedIdentity(bidder_user_a.auth_user_id, bidder_user_a),
        "bidder_b": AuthenticatedIdentity(bidder_user_b.auth_user_id, bidder_user_b),
        "bidder_c": AuthenticatedIdentity(bidder_user_c.auth_user_id, bidder_user_c),
        "officer": AuthenticatedIdentity(officer_user.auth_user_id, officer_user),
    }

    app.dependency_overrides[get_db] = lambda: session
    try:
        yield session, identities, bidder_a, bidder_b, bidder_c, tender, doc_a, doc_b
    finally:
        app.dependency_overrides.clear()
        session.close()


def request_as(identity, method, path, **kwargs):
    app.dependency_overrides[get_authenticated_identity] = lambda: identity
    try:
        return getattr(TestClient(app), method)(path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_authenticated_identity, None)


def test_bidders_me_unauthenticated_returns_401(bidder_workspace_context):
    client = TestClient(app)
    response = client.get("/api/v1/bidders/me")
    assert response.status_code == 401


def test_bidders_me_officer_returns_403(bidder_workspace_context):
    _, identities, _, _, _, _, _, _ = bidder_workspace_context
    response = request_as(identities["officer"], "get", "/api/v1/bidders/me")
    assert response.status_code == 403


def test_bidders_me_bidder_returns_own_profile(bidder_workspace_context):
    _, identities, bidder_a, _, _, _, _, _ = bidder_workspace_context
    response = request_as(identities["bidder_a"], "get", "/api/v1/bidders/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(bidder_a.id)
    assert data["legal_name"] == "Alpha Technologies Pvt Ltd"
    assert data["gst_number"] == "07AAAAA0000A1Z5"
    assert data["pan_number"] == "AAAAA0000A"
    assert data["registration_number"] == "U72200DL2020PTC123456"
    assert data["email"] == "bidder.a@secondlook.local"
    assert data["full_name"] == "Alice Bidder"
    assert data["role"] == "BIDDER"
    assert data["status"] == "VERIFIED"
    assert data["active_tenders_count"] == 1
    assert data["documents_count"] == 1
    assert data["submitted_bids_count"] == 0


def test_bidder_cannot_access_other_bidder_profile(bidder_workspace_context):
    _, identities, _, bidder_b, _, _, _, _ = bidder_workspace_context
    response = request_as(identities["bidder_a"], "get", f"/api/v1/bidders/{bidder_b.id}")
    assert response.status_code == 403


def test_bidder_cannot_access_officer_endpoints(bidder_workspace_context):
    _, identities, _, _, _, tender, _, _ = bidder_workspace_context
    resp_bidders_list = request_as(identities["bidder_a"], "get", "/api/v1/bidders")
    assert resp_bidders_list.status_code == 403

    resp_tender_bidders = request_as(identities["bidder_a"], "get", f"/api/v1/tenders/{tender.id}/bidders")
    assert resp_tender_bidders.status_code == 403

    resp_summary = request_as(identities["bidder_a"], "get", "/api/v1/dashboard/summary")
    assert resp_summary.status_code == 403


def test_new_bidder_empty_counts_are_zero(bidder_workspace_context):
    _, identities, _, _, bidder_c, _, _, _ = bidder_workspace_context
    response = request_as(identities["bidder_c"], "get", "/api/v1/bidders/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(bidder_c.id)
    assert data["legal_name"] == "Gamma Services Ltd"
    assert data["active_tenders_count"] == 0
    assert data["documents_count"] == 0
    assert data["submitted_bids_count"] == 0


def test_bidder_with_documents_reflects_document_count(bidder_workspace_context):
    _, identities, _, bidder_b, _, _, _, _ = bidder_workspace_context
    response = request_as(identities["bidder_b"], "get", "/api/v1/bidders/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(bidder_b.id)
    assert data["documents_count"] == 1
    assert data["active_tenders_count"] == 0
    assert data["submitted_bids_count"] == 0


def test_bidder_can_browse_tenders_read_only(bidder_workspace_context):
    _, identities, _, _, _, tender, _, _ = bidder_workspace_context
    list_resp = request_as(identities["bidder_a"], "get", "/api/v1/tenders")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1
    assert any(t["id"] == str(tender.id) for t in data["items"])

    get_resp = request_as(identities["bidder_a"], "get", f"/api/v1/tenders/{tender.id}")
    assert get_resp.status_code == 200
    tender_data = get_resp.json()
    assert tender_data["title"] == tender.title


def test_tender_listing_response_is_bidder_safe_and_excludes_restricted_data(bidder_workspace_context):
    _, identities, _, _, _, _, _, _ = bidder_workspace_context
    list_resp = request_as(identities["bidder_a"], "get", "/api/v1/tenders")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert "items" in data
    assert len(data["items"]) > 0

    for item in data["items"]:
        # Assert legitimately public tender fields are present
        assert "reference_number" in item
        assert "title" in item
        assert "status" in item

        # Explicitly assert internal officer and other-bidder fields are absent
        assert "bidders" not in item
        assert "internal_comments" not in item
        assert "reviews" not in item
        assert "officer_reviews" not in item
        assert "evaluations" not in item
        assert "compliance_evaluations" not in item
        assert "requirements" not in item
        assert "audit_logs" not in item
        assert "government_verifications" not in item


def test_tender_detail_response_is_bidder_safe_and_excludes_restricted_data(bidder_workspace_context):
    _, identities, _, _, _, tender, _, _ = bidder_workspace_context
    get_resp = request_as(identities["bidder_a"], "get", f"/api/v1/tenders/{tender.id}")
    assert get_resp.status_code == 200
    tender_data = get_resp.json()

    # Assert legitimate public fields
    assert tender_data["reference_number"] == tender.reference_number
    assert tender_data["title"] == tender.title
    assert tender_data["status"] == "ACTIVE"

    # Explicitly assert internal officer and other-bidder fields are absent
    assert "bidders" not in tender_data
    assert "internal_comments" not in tender_data
    assert "reviews" not in tender_data
    assert "officer_reviews" not in tender_data
    assert "evaluations" not in tender_data
    assert "compliance_evaluations" not in tender_data
    assert "requirements" not in tender_data
    assert "audit_logs" not in tender_data
    assert "government_verifications" not in tender_data


def test_bidder_cannot_access_other_bidder_documents_compliance_or_evaluations(bidder_workspace_context):
    _, identities, _, bidder_b, _, tender, _, doc_b = bidder_workspace_context
    bidder_client = identities["bidder_a"]

    # 1. Other bidder's document list -> 403
    resp_docs = request_as(bidder_client, "get", f"/api/v1/bidders/{bidder_b.id}/documents")
    assert resp_docs.status_code == 403

    # 2. Other bidder's document metadata -> 403
    resp_doc = request_as(bidder_client, "get", f"/api/v1/documents/{doc_b.id}")
    assert resp_doc.status_code == 403

    # 3. Other bidder's document signed storage access -> 403
    resp_access = request_as(bidder_client, "get", f"/api/v1/documents/{doc_b.id}/access")
    assert resp_access.status_code == 403

    # 4. Tender officer dashboard -> 403
    resp_dash = request_as(bidder_client, "get", f"/api/v1/tenders/{tender.id}/dashboard")
    assert resp_dash.status_code == 403

    # 5. Tender officer requirements management -> 403
    resp_reqs = request_as(bidder_client, "get", f"/api/v1/tenders/{tender.id}/requirements")
    assert resp_reqs.status_code == 403

