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
from app.models.user import User


@pytest.fixture
def authorization_context():
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
        email="bidder-a@example.test",
        full_name="Bidder A",
        role="BIDDER",
    )
    bidder_user_b = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="bidder-b@example.test",
        full_name="Bidder B",
        role="BIDDER",
    )
    officer_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="officer@example.test",
        full_name="Officer",
        role="OFFICER",
    )
    legacy_user = User(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        email="legacy@example.test",
        full_name="Legacy User",
        role="admin",
    )
    bidder_a = Bidder(user=bidder_user_a, legal_name="Bidder A Ltd")
    bidder_b = Bidder(user=bidder_user_b, legal_name="Bidder B Ltd")
    document_a = Document(
        bidder=bidder_a,
        document_type="GST",
        file_name="bidder-a-gst.pdf",
        status="uploaded",
    )
    document_b = Document(
        bidder=bidder_b,
        document_type="GST",
        file_name="bidder-b-gst.pdf",
        status="uploaded",
    )
    session.add_all([
        bidder_user_a,
        bidder_user_b,
        officer_user,
        legacy_user,
        bidder_a,
        bidder_b,
        document_a,
        document_b,
    ])
    session.commit()

    identities = {
        "bidder_a": AuthenticatedIdentity(bidder_user_a.auth_user_id, bidder_user_a),
        "bidder_b": AuthenticatedIdentity(bidder_user_b.auth_user_id, bidder_user_b),
        "officer": AuthenticatedIdentity(officer_user.auth_user_id, officer_user),
        "legacy": AuthenticatedIdentity(legacy_user.auth_user_id, legacy_user),
    }

    app.dependency_overrides[get_db] = lambda: session
    try:
        yield session, identities, bidder_a, bidder_b, document_a, document_b
    finally:
        app.dependency_overrides.clear()
        session.close()


def request_as(identity, method, path, **kwargs):
    app.dependency_overrides[get_authenticated_identity] = lambda: identity
    try:
        return getattr(TestClient(app), method)(path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_authenticated_identity, None)


def test_bidder_ownership_allows_only_matching_authenticated_user(authorization_context):
    _, identities, bidder_a, bidder_b, _, _ = authorization_context

    own_response = request_as(identities["bidder_a"], "get", f"/api/v1/bidders/{bidder_a.id}")
    foreign_response = request_as(identities["bidder_a"], "get", f"/api/v1/bidders/{bidder_b.id}")
    officer_response = request_as(identities["officer"], "get", f"/api/v1/bidders/{bidder_a.id}")

    assert own_response.status_code == 200
    assert own_response.json()["id"] == str(bidder_a.id)
    assert foreign_response.status_code == 403
    assert officer_response.status_code == 403


def test_bidder_document_boundary_rejects_foreign_bidder_id(authorization_context):
    _, identities, bidder_a, bidder_b, _, _ = authorization_context

    own_response = request_as(identities["bidder_a"], "get", f"/api/v1/bidders/{bidder_a.id}/documents")
    foreign_response = request_as(identities["bidder_a"], "get", f"/api/v1/bidders/{bidder_b.id}/documents")

    assert own_response.status_code == 200
    assert foreign_response.status_code == 403


def test_document_by_id_is_limited_to_owner_or_officer(authorization_context):
    _, identities, _, _, document_a, document_b = authorization_context

    own_response = request_as(identities["bidder_a"], "get", f"/api/v1/documents/{document_a.id}")
    foreign_response = request_as(identities["bidder_a"], "get", f"/api/v1/documents/{document_b.id}")
    officer_response = request_as(identities["officer"], "get", f"/api/v1/documents/{document_a.id}")

    assert own_response.status_code == 200
    assert foreign_response.status_code == 403
    assert officer_response.status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/tenders",
        "/api/v1/tenders/00000000-0000-0000-0000-000000000011",
        "/api/v1/bidders",
        "/api/v1/documents",
        "/api/v1/documents/00000000-0000-0000-0000-000000000001",
        "/api/v1/compliance/evaluations/00000000-0000-0000-0000-000000000001",
        "/api/v1/compliance/evaluations/00000000-0000-0000-0000-000000000001/review",
        "/api/v1/tenders/00000000-0000-0000-0000-000000000011/requirements",
        "/api/v1/tender-requirements/00000000-0000-0000-0000-000000000001",
        "/api/v1/evidence/00000000-0000-0000-0000-000000000001",
        "/api/v1/audit/events",
        "/api/v1/verification/00000000-0000-0000-0000-000000000001",
    ],
)
def test_sensitive_routes_reject_missing_authentication(path):
    response = TestClient(app).get(path)

    assert response.status_code == 401


def test_bidder_cannot_access_requirement_review_or_audit_operations(authorization_context):
    _, identities, _, _, _, _ = authorization_context

    requirement_response = request_as(
        identities["bidder_a"],
        "get",
        "/api/v1/tenders/00000000-0000-0000-0000-000000000011/requirements",
    )
    review_response = request_as(
        identities["bidder_a"],
        "get",
        "/api/v1/compliance/evaluations/00000000-0000-0000-0000-000000000001/review",
    )
    audit_response = request_as(identities["bidder_a"], "get", "/api/v1/audit/events")

    assert requirement_response.status_code == 403
    assert review_response.status_code == 403
    assert audit_response.status_code == 403


def test_bidder_cannot_impersonate_officer_for_requirement_approval(authorization_context):
    _, identities, _, _, _, _ = authorization_context

    response = request_as(
        identities["bidder_a"],
        "post",
        "/api/v1/tender-requirements/00000000-0000-0000-0000-000000000001/approve",
        json={"officer_id": str(identities["officer"].application_user.id)},
    )

    assert response.status_code == 403
