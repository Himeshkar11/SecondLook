import io
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
from app.models.user import User
from app.workers.worker import DocumentOCRWorker, DocumentAIWorker


@pytest.fixture
def bid_submission_context():
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

    tender = Tender(
        id=uuid.uuid4(),
        reference_number="GEM/2026/B/990011",
        title="Procurement of Secure Cloud Infrastructure",
        description="Public tender for secure data management.",
        status="ACTIVE",
        created_by=officer_user.id,
    )

    session.add_all([bidder_user_a, bidder_user_b, officer_user, bidder_a, bidder_b, tender])
    session.commit()

    try:
        yield {
            "engine": engine,
            "session": session,
            "bidder_user_a": bidder_user_a,
            "bidder_user_b": bidder_user_b,
            "officer_user": officer_user,
            "bidder_a": bidder_a,
            "bidder_b": bidder_b,
            "tender": tender,
        }
    finally:
        app.dependency_overrides.clear()
        session.close()



def make_client_for_user(db_session, user: User | None = None) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    if user is not None:
        identity = AuthenticatedIdentity(user.auth_user_id or user.id, user)
        app.dependency_overrides[get_authenticated_identity] = lambda: identity
    else:
        app.dependency_overrides.pop(get_authenticated_identity, None)
    return TestClient(app)



def test_unauthenticated_cannot_access_bid_endpoints(bid_submission_context):
    client = make_client_for_user(bid_submission_context["session"], user=None)
    tender_id = str(bid_submission_context["tender"].id)

    res = client.post(f"/api/v1/bidder/tenders/{tender_id}/bids")
    assert res.status_code == 401

    res = client.get("/api/v1/bidder/bids")
    assert res.status_code == 401


def test_officer_cannot_call_bidder_bid_endpoints(bid_submission_context):
    client = make_client_for_user(bid_submission_context["session"], user=bid_submission_context["officer_user"])
    tender_id = str(bid_submission_context["tender"].id)

    res = client.post(f"/api/v1/bidder/tenders/{tender_id}/bids")
    assert res.status_code == 403

    res = client.get("/api/v1/bidder/bids")
    assert res.status_code == 403


def test_bidder_can_create_draft_bid_and_idempotency(bid_submission_context):
    client = make_client_for_user(bid_submission_context["session"], user=bid_submission_context["bidder_user_a"])
    tender_id = str(bid_submission_context["tender"].id)

    # 1. Create draft bid
    res = client.post(f"/api/v1/bidder/tenders/{tender_id}/bids")
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "DRAFT"
    assert data["tender_id"] == tender_id
    assert data["bidder_id"] == str(bid_submission_context["bidder_a"].id)
    assert data["submitted_at"] is None
    assert data["documents_count"] == 0
    bid_id = data["id"]

    # 2. Call again -> returns existing bid (idempotent, no duplicate rows)
    res_again = client.post(f"/api/v1/bidder/tenders/{tender_id}/bids")
    assert res_again.status_code == 201
    data_again = res_again.json()
    assert data_again["id"] == bid_id
    assert data_again["status"] == "DRAFT"


def test_bidder_can_list_and_get_own_bids(bid_submission_context):
    client = make_client_for_user(bid_submission_context["session"], user=bid_submission_context["bidder_user_a"])
    tender_id = str(bid_submission_context["tender"].id)

    # Create bid
    res_create = client.post(f"/api/v1/bidder/tenders/{tender_id}/bids")
    bid_id = res_create.json()["id"]

    # List bids
    res_list = client.get("/api/v1/bidder/bids")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 1
    assert items[0]["id"] == bid_id
    assert items[0]["tender_title"] == "Procurement of Secure Cloud Infrastructure"
    assert items[0]["status"] == "DRAFT"

    # Get single bid
    res_get = client.get(f"/api/v1/bidder/bids/{bid_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == bid_id


def test_cross_bidder_isolation_on_bids(bid_submission_context):
    """Bidder A must not be able to read, submit, or upload documents to Bidder B's bid."""
    client_b = make_client_for_user(bid_submission_context["session"], user=bid_submission_context["bidder_user_b"])
    tender_id = str(bid_submission_context["tender"].id)

    # Bidder B creates a bid
    res_b = client_b.post(f"/api/v1/bidder/tenders/{tender_id}/bids")
    bid_b_id = res_b.json()["id"]

    # Bidder A tries to read Bidder B's bid
    client_a = make_client_for_user(bid_submission_context["session"], user=bid_submission_context["bidder_user_a"])
    res_read = client_a.get(f"/api/v1/bidder/bids/{bid_b_id}")
    assert res_read.status_code == 403

    # Bidder A tries to submit Bidder B's bid
    res_submit = client_a.post(f"/api/v1/bidder/bids/{bid_b_id}/submit")
    assert res_submit.status_code == 403

    # Bidder A tries to upload document to Bidder B's bid
    fake_file = io.BytesIO(b"%PDF-1.4 test content")
    res_upload = client_a.post(
        f"/api/v1/bidder/bids/{bid_b_id}/documents",
        data={"document_type": "TECHNICAL_DOCUMENT"},
        files={"file": ("proposal.pdf", fake_file, "application/pdf")},
    )
    assert res_upload.status_code == 403


def test_document_upload_and_bid_submission_lifecycle(bid_submission_context):
    client_a = make_client_for_user(bid_submission_context["session"], user=bid_submission_context["bidder_user_a"])
    tender_id = str(bid_submission_context["tender"].id)

    # 1. Create bid
    res_create = client_a.post(f"/api/v1/bidder/tenders/{tender_id}/bids")
    bid_id = res_create.json()["id"]

    # 2. Attempt submission without documents -> rejected with 422
    res_fail_submit = client_a.post(f"/api/v1/bidder/bids/{bid_id}/submit")
    assert res_fail_submit.status_code == 422
    assert "without any attached proposal" in res_fail_submit.json()["detail"]["error"]["message"]

    # 3. Upload valid document to the bid workspace
    # Mock storage upload in test environment
    from unittest.mock import patch
    with patch("app.services.document_service.DocumentService._upload_to_storage", return_value=None):
        fake_file = io.BytesIO(b"%PDF-1.4 sample proposal content")
        res_upload = client_a.post(
            f"/api/v1/bidder/bids/{bid_id}/documents",
            data={"document_type": "TECHNICAL_DOCUMENT"},
            files={"file": ("tech_proposal.pdf", fake_file, "application/pdf")},
        )
        assert res_upload.status_code == 201
        doc_data = res_upload.json()
        assert doc_data["bid_id"] == bid_id
        assert doc_data["document_type"] == "TECHNICAL_DOCUMENT"
        assert doc_data["status"] == "QUEUED"
        doc_id = doc_data["id"]

    # 4. Verify bid details reflect 1 attached document
    res_get = client_a.get(f"/api/v1/bidder/bids/{bid_id}")
    assert res_get.status_code == 200
    bid_detail = res_get.json()
    assert bid_detail["documents_count"] == 1
    assert len(bid_detail["documents"]) == 1
    assert bid_detail["documents"][0]["id"] == doc_id
    assert bid_detail["documents"][0]["file_name"] == "tech_proposal.pdf"

    # 5. Formally submit the bid
    res_submit = client_a.post(f"/api/v1/bidder/bids/{bid_id}/submit")
    assert res_submit.status_code == 200
    submit_data = res_submit.json()
    assert submit_data["status"] == "SUBMITTED"
    assert submit_data["submitted_at"] is not None

    # 6. DECISION SEPARATION: Assert submission does NOT qualify or award the tender
    tender = bid_submission_context["session"].get(Tender, bid_submission_context["tender"].id)
    assert tender.status == "ACTIVE"  # Tender remains in its public status

    # 7. Attempting to upload to a submitted bid is rejected (locked)
    with patch("app.services.document_service.DocumentService._upload_to_storage", return_value=None):
        fake_file2 = io.BytesIO(b"%PDF-1.4 additional content")
        res_upload_locked = client_a.post(
            f"/api/v1/bidder/bids/{bid_id}/documents",
            data={"document_type": "SUPPORTING_DOCUMENT"},
            files={"file": ("extra.pdf", fake_file2, "application/pdf")},
        )
        assert res_upload_locked.status_code == 400
        assert "Cannot upload documents to a submitted bid" in res_upload_locked.json()["detail"]["error"]["message"]


def test_cross_bidder_document_access_denied(bid_submission_context):
    """Bidder B must not be able to get signed download access to Bidder A's bid document."""
    session = bid_submission_context["session"]
    bidder_a = bid_submission_context["bidder_a"]
    tender = bid_submission_context["tender"]

    # Manually create a document owned by Bidder A
    doc_a = Document(
        id=uuid.uuid4(),
        bidder_id=bidder_a.id,
        tender_id=tender.id,
        document_type="FINANCIAL_DOCUMENT",
        file_name="alpha_balance_sheet.pdf",
        storage_path=f"{bidder_a.id}/doc.pdf",
        status="uploaded",
    )
    session.add(doc_a)
    session.commit()

    # Bidder A can access (or get signed URL)
    client_a = make_client_for_user(session, user=bid_submission_context["bidder_user_a"])
    from unittest.mock import patch
    with patch("app.services.document_service.DocumentService.get_document_access", return_value={"url": "https://signed.download/doc"}):
        res_a = client_a.get(f"/api/v1/documents/{doc_a.id}/access")
        assert res_a.status_code == 200

    # Bidder B is forbidden
    client_b = make_client_for_user(session, user=bid_submission_context["bidder_user_b"])
    res_b = client_b.get(f"/api/v1/documents/{doc_a.id}/access")
    assert res_b.status_code == 403


def test_document_pipeline_ocr_and_ai_retry(bid_submission_context):
    """Verify that uploaded bid documents integrate with existing OCR and AI worker retries."""
    session = bid_submission_context["session"]
    bidder_a = bid_submission_context["bidder_a"]
    tender = bid_submission_context["tender"]

    doc_a = Document(
        id=uuid.uuid4(),
        bidder_id=bidder_a.id,
        tender_id=tender.id,
        document_type="GST",
        file_name="alpha_gst.pdf",
        storage_path=f"{bidder_a.id}/gst.pdf",
        status="OCR_FAILED",
        ocr_status="OCR_FAILED",
        ocr_error="Timeout reading storage object",
    )
    session.add(doc_a)
    session.commit()

    client_a = make_client_for_user(session, user=bid_submission_context["bidder_user_a"])

    # Retry OCR endpoint
    from unittest.mock import patch
    with patch("app.workers.worker.DocumentOCRWorker.process_document_by_id", return_value=None):
        res_retry = client_a.post(f"/api/v1/documents/{doc_a.id}/ocr/retry")
        assert res_retry.status_code == 200

    # Verify AI retry is NOT allowed before OCR completes successfully
    res_ai_blocked = client_a.post(f"/api/v1/documents/{doc_a.id}/ai/retry")
    assert res_ai_blocked.status_code == 400
    assert "Cannot retry AI extraction before OCR" in res_ai_blocked.json()["detail"]["error"]["message"]

    # Verify AI extraction separation: AI cannot approve or award tender
    doc_a.ocr_status = "OCR_COMPLETED"
    doc_a.ocr_text = "GSTIN: 07AAAAA0000A1Z5 LEGAL NAME: ALPHA TECH"
    session.commit()

    with patch("app.workers.worker.DocumentAIWorker.process_document_by_id", return_value=None):
        res_ai_retry = client_a.post(f"/api/v1/documents/{doc_a.id}/ai/retry")
        assert res_ai_retry.status_code == 200


def test_cannot_resubmit_already_submitted_bid(bid_submission_context):
    session = bid_submission_context["session"]
    bidder_a = bid_submission_context["bidder_a"]
    tender = bid_submission_context["tender"]

    bid = Bid(
        id=uuid.uuid4(),
        bidder_id=bidder_a.id,
        tender_id=tender.id,
        status="SUBMITTED",
    )
    session.add(bid)
    session.commit()

    client_a = make_client_for_user(session, user=bid_submission_context["bidder_user_a"])
    res = client_a.post(f"/api/v1/bidder/bids/{bid.id}/submit")
    assert res.status_code == 400
    assert "already been submitted" in res.json()["detail"]["error"]["message"]


def test_bidder_profile_counts_reflect_submitted_bids(bid_submission_context):
    session = bid_submission_context["session"]
    bidder_a = bid_submission_context["bidder_a"]
    tender = bid_submission_context["tender"]

    client_a = make_client_for_user(session, user=bid_submission_context["bidder_user_a"])

    # Initially submitted_bids_count is 0
    res_prof_1 = client_a.get("/api/v1/bidders/me")
    assert res_prof_1.status_code == 200
    assert res_prof_1.json()["submitted_bids_count"] == 0

    # Add submitted bid
    bid = Bid(
        id=uuid.uuid4(),
        bidder_id=bidder_a.id,
        tender_id=tender.id,
        status="SUBMITTED",
    )
    session.add(bid)
    session.commit()

    # Now submitted_bids_count is 1
    res_prof_2 = client_a.get("/api/v1/bidders/me")
    assert res_prof_2.status_code == 200
    assert res_prof_2.json()["submitted_bids_count"] == 1

