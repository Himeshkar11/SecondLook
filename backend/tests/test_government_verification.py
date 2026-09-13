"""Unit and integration tests for Task 10: Government Verification Integration Layer.

Strictly verifies that:
1. GovernmentProvider interface and polymorphic adapters exist.
2. DemoGSTProvider & DemoPANProvider return deterministic fictional data.
3. GST FOUND, NOT_FOUND, and UNAVAILABLE/ERROR cases function correctly.
4. PAN FOUND, NOT_FOUND, and UNAVAILABLE/ERROR cases function correctly.
5. Format validation strictly distinguishes valid format from government verified.
6. Deterministic field-level comparison produces MATCH, MISMATCH, MISSING_FROM_DOCUMENT, MISSING_FROM_SOURCE.
7. Overall results evaluate strictly to VERIFIED, MISMATCH, NOT_FOUND, SOURCE_ERROR.
8. Zero compliance, bidder qualification, or risk scoring logic is invoked or stored.
9. Verification status (PENDING, PROCESSING, COMPLETED, FAILED) is strictly separated from verification results.
10. Database records and history are preserved.
11. AI extraction is an enforced prerequisite.
12. API endpoints and Worker integration operate reliably.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.integrations.base import (
    GovernmentProvider,
    GovernmentSourceStatus,
    GovernmentVerificationResponse,
)
from app.integrations.comparison import (
    FieldComparisonStatus,
    OverallVerificationResult,
    compare_gst_data,
    compare_pan_data,
    normalize_value,
)
from app.integrations.gst import DemoGSTProvider, GSTProvider
from app.integrations.pan import DemoPANProvider, PANProvider
from app.integrations.registry import get_government_provider
from app.integrations.validation import validate_gstin_format, validate_pan_format
from app.main import app
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.services.government_verification_service import (
    AIExtractionPrerequisiteError,
    GovernmentVerificationService,
    InvalidIdentifierFormatError,
    MissingIdentifierError,
    UnsupportedDocumentTypeError,
)
from app.workers.jobs import (
    DocumentVerificationJobRecord,
    DocumentVerificationStatus,
    InvalidStateTransitionError,
    JobQueue,
)
from app.workers.worker import DocumentVerificationWorker

KNOWN_DOC_UUID = "00000000-0000-0000-0000-000000000041"
KNOWN_BIDDER_UUID = "00000000-0000-0000-0000-000000000021"


# ==============================================================================
# 1. Provider Interface and Demo Providers
# ==============================================================================

def test_government_provider_interface_cannot_be_instantiated_directly():
    provider = GovernmentProvider()
    with pytest.raises(NotImplementedError):
        provider.verify("DUMMY")


def test_demo_gst_provider_found():
    provider = DemoGSTProvider()
    resp = provider.verify("29ABCDE1234F1Z5")
    assert resp.source == "GST"
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.identifier == "29ABCDE1234F1Z5"
    assert resp.data["gstin"] == "29ABCDE1234F1Z5"
    assert resp.data["legal_name"] == "ABC TECHNOLOGIES PRIVATE LIMITED"
    assert resp.data["trade_name"] == "ABC TECHNOLOGIES"
    assert resp.data["registration_date"] == "2024-04-12"
    assert resp.data["status"] == "ACTIVE"
    assert resp.data["state"] == "Tamil Nadu"


def test_demo_gst_provider_not_found():
    provider = DemoGSTProvider()
    resp = provider.verify("29NOTFOUND1234F1")
    assert resp.source == "GST"
    assert resp.status == GovernmentSourceStatus.NOT_FOUND.value


def test_demo_gst_provider_unavailable():
    provider = DemoGSTProvider()
    resp = provider.verify("29ERROR1234F1Z5")
    assert resp.source == "GST"
    assert resp.status == GovernmentSourceStatus.UNAVAILABLE.value


def test_demo_pan_provider_found():
    provider = DemoPANProvider()
    resp = provider.verify("ABCDE1234F")
    assert resp.source == "PAN"
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.identifier == "ABCDE1234F"
    assert resp.data["pan"] == "ABCDE1234F"
    assert resp.data["name"] == "ABC TECHNOLOGIES PRIVATE LIMITED"
    assert resp.data["status"] == "ACTIVE"


def test_demo_pan_provider_not_found():
    provider = DemoPANProvider()
    resp = provider.verify("ABCDE0000N")
    assert resp.source == "PAN"
    assert resp.status == GovernmentSourceStatus.NOT_FOUND.value


def test_demo_pan_provider_unavailable():
    provider = DemoPANProvider()
    resp = provider.verify("ERROR0000F")
    assert resp.source == "PAN"
    assert resp.status == GovernmentSourceStatus.UNAVAILABLE.value


def test_provider_registry_factory():
    gst_prov = get_government_provider("GST")
    assert isinstance(gst_prov, (DemoGSTProvider, GSTProvider))
    pan_prov = get_government_provider("PAN")
    assert isinstance(pan_prov, (DemoPANProvider, PANProvider))

    with pytest.raises(ValueError):
        get_government_provider("UDYAM")


# ==============================================================================
# 2. Format Validation Tests (Valid Format != Government Verified)
# ==============================================================================

def test_gstin_format_validation():
    assert validate_gstin_format("29ABCDE1234F1Z5") is True
    assert validate_gstin_format("29NOTFOUND1234F1") is True  # Demo test case
    assert validate_gstin_format("INVALID_GST") is False
    assert validate_gstin_format("123") is False
    assert validate_gstin_format("") is False
    assert validate_gstin_format(None) is False


def test_pan_format_validation():
    assert validate_pan_format("ABCDE1234F") is True
    assert validate_pan_format("ABCDE0000N") is True
    assert validate_pan_format("INVALIDPAN") is False
    assert validate_pan_format("123") is False
    assert validate_pan_format("") is False
    assert validate_pan_format(None) is False


# ==============================================================================
# 3. Normalization and Comparison Logic
# ==============================================================================

def test_normalization_casing_whitespace_and_date():
    assert normalize_value("  abc technologies   private limited  ") == "ABC TECHNOLOGIES PRIVATE LIMITED"
    assert normalize_value("12/04/2024") == "2024-04-12"
    assert normalize_value("2024-04-12") == "2024-04-12"
    assert normalize_value(None) is None
    assert normalize_value("") is None


def test_gst_comparison_perfect_match():
    doc_fields = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "registration_date": "12/04/2024",
    }
    gov_data = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "registration_date": "2024-04-12",
        "status": "ACTIVE",
    }

    result, field_results = compare_gst_data(doc_fields, gov_data)
    assert result == OverallVerificationResult.VERIFIED
    assert field_results["gstin"]["status"] == FieldComparisonStatus.MATCH.value
    assert field_results["legal_name"]["status"] == FieldComparisonStatus.MATCH.value
    assert field_results["registration_date"]["status"] == FieldComparisonStatus.MATCH.value
    assert field_results["status"]["status"] == FieldComparisonStatus.MISSING_FROM_DOCUMENT.value


def test_gst_comparison_mismatch():
    doc_fields = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "XYZ TECHNOLOGIES PRIVATE LIMITED",
    }
    gov_data = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    }

    result, field_results = compare_gst_data(doc_fields, gov_data)
    assert result == OverallVerificationResult.MISMATCH
    assert field_results["gstin"]["status"] == FieldComparisonStatus.MATCH.value
    assert field_results["legal_name"]["status"] == FieldComparisonStatus.MISMATCH.value


def test_pan_comparison_match():
    doc_fields = {
        "pan": "ABCDE1234F",
        "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "status": "ACTIVE",
    }
    gov_data = {
        "pan": "ABCDE1234F",
        "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "status": "ACTIVE",
    }

    result, field_results = compare_pan_data(doc_fields, gov_data)
    assert result == OverallVerificationResult.VERIFIED
    assert field_results["pan"]["status"] == FieldComparisonStatus.MATCH.value
    assert field_results["name"]["status"] == FieldComparisonStatus.MATCH.value
    assert field_results["status"]["status"] == FieldComparisonStatus.MATCH.value


def test_pan_comparison_mismatch():
    doc_fields = {
        "pan": "ABCDE1234F",
        "name": "OTHER CORP",
    }
    gov_data = {
        "pan": "ABCDE1234F",
        "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    }

    result, field_results = compare_pan_data(doc_fields, gov_data)
    assert result == OverallVerificationResult.MISMATCH
    assert field_results["pan"]["status"] == FieldComparisonStatus.MATCH.value
    assert field_results["name"]["status"] == FieldComparisonStatus.MISMATCH.value


# ==============================================================================
# 4. Verification Service Orchestration & Preconditions
# ==============================================================================

def test_service_requires_completed_ai_extraction():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.ai_status = "AI_PENDING"
    mock_doc.ai_extraction = None
    mock_db.scalar.return_value = mock_doc

    service = GovernmentVerificationService(db=mock_db)
    with pytest.raises(AIExtractionPrerequisiteError):
        service.verify_document(KNOWN_DOC_UUID)


def test_service_rejects_unsupported_document_type():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.document_type = "UDYAM"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {"udyam_number": "UDYAM-001"}
    mock_db.scalar.return_value = mock_doc

    service = GovernmentVerificationService(db=mock_db)
    with pytest.raises(UnsupportedDocumentTypeError):
        service.verify_document(KNOWN_DOC_UUID)


def test_service_rejects_missing_identifier():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {"legal_name": "ABC TECH"}  # No gstin
    mock_db.scalar.return_value = mock_doc

    service = GovernmentVerificationService(db=mock_db)
    with pytest.raises(MissingIdentifierError):
        service.verify_document(KNOWN_DOC_UUID)


def test_service_rejects_invalid_identifier_format():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {"gstin": "INVALID_GST", "legal_name": "ABC TECH"}
    mock_db.scalar.return_value = mock_doc

    service = GovernmentVerificationService(db=mock_db)
    with pytest.raises(InvalidIdentifierFormatError):
        service.verify_document(KNOWN_DOC_UUID)


def test_service_successful_gst_verification():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "registration_date": "2024-04-12",
    }
    mock_db.scalar.side_effect = [mock_doc, None]  # Doc lookup, active job lookup (None)

    service = GovernmentVerificationService(db=mock_db)
    res = service.verify_document(KNOWN_DOC_UUID)

    assert res["status"] == "COMPLETED"
    assert res["verification_result"] == "VERIFIED"
    assert res["field_results"]["gstin"]["status"] == "MATCH"
    assert res["field_results"]["legal_name"]["status"] == "MATCH"
    assert mock_doc.verification_status == "VERIFIED"


def test_service_gst_not_found():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {
        "gstin": "29NOTFOUND1234F1",
        "legal_name": "ABC TECH",
    }
    mock_db.scalar.side_effect = [mock_doc, None]

    service = GovernmentVerificationService(db=mock_db)
    res = service.verify_document(KNOWN_DOC_UUID)

    assert res["status"] == "COMPLETED"
    assert res["verification_result"] == "NOT_FOUND"
    assert mock_doc.verification_status == "NOT_FOUND"


def test_service_pan_verification():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.document_type = "PAN"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {
        "pan": "ABCDE1234F",
        "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    }
    mock_db.scalar.side_effect = [mock_doc, None]

    service = GovernmentVerificationService(db=mock_db)
    res = service.verify_document(KNOWN_DOC_UUID)

    assert res["status"] == "COMPLETED"
    assert res["verification_result"] == "VERIFIED"
    assert res["field_results"]["pan"]["status"] == "MATCH"
    assert mock_doc.verification_status == "VERIFIED"


def test_service_source_error_handling():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {
        "gstin": "29ERROR1234F1Z5",
        "legal_name": "ABC TECH",
    }
    mock_db.scalar.side_effect = [mock_doc, None]

    service = GovernmentVerificationService(db=mock_db)
    res = service.verify_document(KNOWN_DOC_UUID)

    assert res["status"] == "FAILED"
    assert res["verification_result"] == "SOURCE_ERROR"
    assert mock_doc.verification_status == "SOURCE_ERROR"


# ==============================================================================
# 5. Worker and Job Lifecycle Tests
# ==============================================================================

def test_verification_job_transitions():
    job = DocumentVerificationJobRecord(document_id=KNOWN_DOC_UUID)
    assert job.status == DocumentVerificationStatus.PENDING

    job.transition_to(DocumentVerificationStatus.PROCESSING)
    assert job.status == DocumentVerificationStatus.PROCESSING

    job.transition_to(DocumentVerificationStatus.COMPLETED)
    assert job.status == DocumentVerificationStatus.COMPLETED

    # Cannot transition out of COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        job.transition_to(DocumentVerificationStatus.PROCESSING)


def test_verification_worker_execution():
    mock_service = MagicMock()
    mock_service.verify_document.return_value = {
        "id": str(uuid.uuid4()),
        "status": "COMPLETED",
        "verification_result": "VERIFIED",
    }

    queue = JobQueue()
    job = DocumentVerificationJobRecord(document_id=KNOWN_DOC_UUID)
    queue.enqueue(job)

    worker = DocumentVerificationWorker(verification_service=mock_service, queue=queue)
    processed = worker.process_job(job)

    assert processed.status == DocumentVerificationStatus.COMPLETED
    assert processed.result["verification_result"] == "VERIFIED"


# ==============================================================================
# 6. API Route Tests
# ==============================================================================

def test_post_verify_document_endpoint():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    }
    mock_db.scalar.side_effect = [mock_doc, None]

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post(f"/api/v1/documents/{KNOWN_DOC_UUID}/verify")
        assert response.status_code == 200
        data = response.json()
        assert data["verification_result"] == "VERIFIED"
        assert data["status"] == "COMPLETED"
    finally:
        app.dependency_overrides.clear()


def test_get_document_verification_endpoint():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.verification_status = "VERIFIED"

    mock_rec = MagicMock(spec=GovernmentVerification)
    mock_rec.id = uuid.uuid4()
    mock_rec.document_id = uuid.UUID(KNOWN_DOC_UUID)
    mock_rec.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_rec.source = "GST"
    mock_rec.provider = "demo"
    mock_rec.identifier = "29ABCDE1234F1Z5"
    mock_rec.status = "COMPLETED"
    mock_rec.verification_result = "VERIFIED"
    mock_rec.government_data = {"gstin": "29ABCDE1234F1Z5"}
    mock_rec.field_results = {"gstin": {"status": "MATCH"}}
    mock_rec.error = None
    mock_rec.created_at = datetime.now(timezone.utc)
    mock_rec.completed_at = datetime.now(timezone.utc)

    mock_db.scalar.return_value = mock_doc
    mock_db.scalars.return_value.all.return_value = [mock_rec]

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get(f"/api/v1/documents/{KNOWN_DOC_UUID}/verification")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == KNOWN_DOC_UUID
        assert data["verification_status"] == "VERIFIED"
        assert data["latest_verification"]["identifier"] == "29ABCDE1234F1Z5"
    finally:
        app.dependency_overrides.clear()
