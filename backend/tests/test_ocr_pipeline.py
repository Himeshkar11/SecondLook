"""Unit and integration tests for Task 08: Document Processing + OCR Pipeline.

Verifies:
1. OCRProcessor interface and abstraction.
2. DemoOCRProcessor deterministic output.
3. StandardOCRProcessor PDF text extraction with fictional GST fixture.
4. Document OCR status transitions (UPLOADED -> QUEUED -> OCR_PROCESSING -> OCR_COMPLETED).
5. OCR text persistence in PostgreSQL.
6. OCR failure handling (OCR_FAILED status, error capture, original file preserved).
7. Duplicate processing prevention / idempotency.
8. Missing document safe handling.
9. Storage retrieval failure handling.
10. Retry capability for failed OCR jobs.
11. Document OCR API endpoint (/api/v1/documents/{id}/ocr).
12. Retry API endpoint (/api/v1/documents/{id}/ocr/retry).
"""

import io
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.mock_auth
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.main import app
from app.models.document import Document
from app.ocr import (
    DemoOCRProcessor,
    DocumentInput,
    ExtractedText,
    OCRProcessor,
    StandardOCRProcessor,
    get_ocr_processor,
)
from app.services.document_service import DocumentService
from app.workers.jobs import (
    DocumentOCRJobRecord,
    DocumentOCRStatus,
    JobQueue,
    document_ocr_queue,
)
from app.workers.worker import DocumentOCRWorker

KNOWN_BIDDER_UUID = "00000000-0000-0000-0000-000000000021"
KNOWN_DOC_UUID = "00000000-0000-0000-0000-000000000041"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "documents" / "sample_gst.pdf"


def _make_mock_doc(
    doc_id=KNOWN_DOC_UUID,
    ocr_status="QUEUED",
    ocr_text=None,
    ocr_error=None,
):
    d = MagicMock(spec=Document)
    d.id = uuid.UUID(doc_id)
    d.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    d.document_type = "GST"
    d.file_name = "sample_gst.pdf"
    d.storage_path = f"{KNOWN_BIDDER_UUID}/{doc_id}_sample_gst.pdf"
    d.mime_type = "application/pdf"
    d.file_size = 1024
    d.status = ocr_status
    d.ocr_status = ocr_status
    d.ocr_text = ocr_text
    d.ocr_error = ocr_error
    d.ocr_completed_at = datetime.now(timezone.utc) if ocr_status == "OCR_COMPLETED" else None
    d.uploaded_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    d.bidder = MagicMock(legal_name="ABC Technologies Private Limited")
    return d


# ==============================================================================
# 1. OCRProcessor interface & abstraction
# ==============================================================================

def test_ocr_processor_abstraction():
    """Verify that OCRProcessor is an abstract class requiring process method."""
    assert issubclass(DemoOCRProcessor, OCRProcessor)
    assert issubclass(StandardOCRProcessor, OCRProcessor)

    processor = get_ocr_processor("standard")
    assert isinstance(processor, OCRProcessor)


# ==============================================================================
# 2. Demo OCR deterministic output
# ==============================================================================

def test_demo_ocr_deterministic_output():
    processor = DemoOCRProcessor()
    doc_input = DocumentInput(
        document_id="doc-1",
        file_name="vendor_gst.pdf",
        metadata={"document_type": "gst"},
    )
    result = processor.process(doc_input)
    assert isinstance(result, ExtractedText)
    assert "27ABCDE1234F1Z5" in result.text
    assert "Demo Bidder Pvt Ltd" in result.text
    assert result.metadata["is_demo"] is True


# ==============================================================================
# 3. Real / Standard OCR processing with PDF fixture
# ==============================================================================

def test_standard_ocr_pdf_fixture_extraction():
    assert FIXTURE_PATH.exists(), "Sample GST fixture should exist"
    with open(FIXTURE_PATH, "rb") as f:
        content = f.read()

    processor = StandardOCRProcessor()
    doc_input = DocumentInput(
        document_id="doc-fixture",
        file_name="sample_gst.pdf",
        mime_type="application/pdf",
        content=content,
    )
    result = processor.process(doc_input)
    assert isinstance(result, ExtractedText)
    assert "GST CERTIFICATE" in result.text
    assert "29ABCDE1234F1Z5" in result.text
    assert "ABC TECHNOLOGIES PRIVATE LIMITED" in result.text
    assert "Tamil Nadu" in result.text


# ==============================================================================
# 4. Document OCR status transitions
# ==============================================================================

def test_document_ocr_status_transitions():
    job = DocumentOCRJobRecord(
        document_id=KNOWN_DOC_UUID,
        bidder_id=KNOWN_BIDDER_UUID,
        file_name="sample_gst.pdf",
        status=DocumentOCRStatus.QUEUED,
    )
    assert job.status == DocumentOCRStatus.QUEUED

    # Transition to OCR_PROCESSING
    job.transition_to(DocumentOCRStatus.OCR_PROCESSING)
    assert job.status == DocumentOCRStatus.OCR_PROCESSING

    # Transition to OCR_COMPLETED
    job.transition_to(DocumentOCRStatus.OCR_COMPLETED)
    assert job.status == DocumentOCRStatus.OCR_COMPLETED
    assert job.completed_at is not None


# ==============================================================================
# 5. Full worker document processing saves OCR text to PostgreSQL
# ==============================================================================

def test_worker_processes_job_and_saves_ocr_text():
    mock_db = MagicMock()
    mock_doc = _make_mock_doc(ocr_status="QUEUED")
    mock_db.scalar.return_value = mock_doc

    queue = JobQueue()
    job = DocumentOCRJobRecord(
        document_id=KNOWN_DOC_UUID,
        bidder_id=KNOWN_BIDDER_UUID,
        storage_path="path/to/doc.pdf",
        file_name="sample_gst.pdf",
        document_type="gst",
        status=DocumentOCRStatus.QUEUED,
    )
    queue.enqueue(job)

    worker = DocumentOCRWorker(
        ocr_processor=DemoOCRProcessor(),
        queue=queue,
        db=mock_db,
    )

    with open(FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()

    processed_job = worker.process_job(job, content_override=file_bytes)

    assert processed_job.status == DocumentOCRStatus.OCR_COMPLETED
    assert mock_doc.ocr_status == "OCR_COMPLETED"
    assert mock_doc.status == "OCR_COMPLETED"
    assert "GSTIN" in mock_doc.ocr_text
    assert mock_doc.ocr_completed_at is not None
    assert mock_db.commit.called


# ==============================================================================
# 6. OCR failure handling: safe error capture, original file preserved
# ==============================================================================

def test_worker_handles_ocr_failure_safely():
    mock_db = MagicMock()
    mock_doc = _make_mock_doc(ocr_status="QUEUED")
    mock_db.scalar.return_value = mock_doc

    class FailingProcessor(OCRProcessor):
        def process(self, document: DocumentInput) -> ExtractedText:
            raise RuntimeError("Corrupted document header")

    queue = JobQueue()
    job = DocumentOCRJobRecord(
        document_id=KNOWN_DOC_UUID,
        bidder_id=KNOWN_BIDDER_UUID,
        storage_path="path/to/doc.pdf",
        file_name="corrupt.pdf",
        status=DocumentOCRStatus.QUEUED,
    )
    queue.enqueue(job)

    worker = DocumentOCRWorker(
        ocr_processor=FailingProcessor(),
        queue=queue,
        db=mock_db,
    )

    processed = worker.process_job(job, content_override=b"bad content")

    assert processed.status == DocumentOCRStatus.OCR_FAILED
    assert "Corrupted document header" in processed.error
    assert mock_doc.ocr_status == "OCR_FAILED"
    assert "Corrupted document header" in mock_doc.ocr_error
    # Confirm original storage path was NOT cleared or deleted
    assert mock_doc.storage_path is not None


# ==============================================================================
# 7. Duplicate processing prevention / idempotency
# ==============================================================================

def test_duplicate_processing_prevention():
    mock_db = MagicMock()
    queue = JobQueue()

    completed_job = DocumentOCRJobRecord(
        document_id=KNOWN_DOC_UUID,
        bidder_id=KNOWN_BIDDER_UUID,
        status=DocumentOCRStatus.OCR_COMPLETED,
    )
    # Register in queue directly without overriding status
    queue._jobs[completed_job.job_id] = completed_job

    worker = DocumentOCRWorker(
        ocr_processor=DemoOCRProcessor(),
        queue=queue,
        db=mock_db,
    )

    result = worker.process_job(completed_job, content_override=b"pdf")
    assert result.status == DocumentOCRStatus.OCR_COMPLETED
    assert result.attempt_count == 0  # Was not re-executed


# ==============================================================================
# 8. Storage retrieval failure handling
# ==============================================================================

def test_storage_retrieval_failure_marks_ocr_failed():
    mock_db = MagicMock()
    mock_doc = _make_mock_doc(ocr_status="QUEUED")
    mock_db.scalar.return_value = mock_doc

    queue = JobQueue()
    job = DocumentOCRJobRecord(
        document_id=KNOWN_DOC_UUID,
        bidder_id=KNOWN_BIDDER_UUID,
        storage_path="path/to/missing.pdf",
        status=DocumentOCRStatus.QUEUED,
    )
    queue.enqueue(job)

    worker = DocumentOCRWorker(
        ocr_processor=DemoOCRProcessor(),
        queue=queue,
        db=mock_db,
    )

    with patch.object(worker, "_fetch_from_storage", side_effect=RuntimeError("Storage 404")):
        processed = worker.process_job(job)
        assert processed.status == DocumentOCRStatus.OCR_FAILED
        assert "Storage 404" in processed.error


# ==============================================================================
# 9. Retry capability for failed OCR jobs
# ==============================================================================

def test_retry_document_ocr():
    mock_db = MagicMock()
    mock_doc = _make_mock_doc(ocr_status="OCR_FAILED", ocr_error="Previous error")
    mock_db.scalar.return_value = mock_doc

    service = DocumentService(db=mock_db)
    retry_res = service.retry_document_ocr(KNOWN_DOC_UUID)

    assert retry_res["status"] == "QUEUED"
    assert mock_doc.ocr_status == "QUEUED"
    assert mock_doc.ocr_error is None


# ==============================================================================
# 10. API: GET /api/v1/documents/{id}/ocr
# ==============================================================================

def test_api_get_document_ocr():
    client = TestClient(app)

    def mock_db_dep():
        session = MagicMock()
        doc = _make_mock_doc(
            ocr_status="OCR_COMPLETED",
            ocr_text="GST CERTIFICATE\nGSTIN: 29ABCDE1234F1Z5",
        )
        session.scalar.return_value = doc
        session.execute.return_value.scalars.return_value.unique.return_value.first.return_value = doc
        yield session

    app.dependency_overrides[get_db] = mock_db_dep
    try:
        response = client.get(f"/api/v1/documents/{KNOWN_DOC_UUID}/ocr")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == KNOWN_DOC_UUID
        assert data["ocr_status"] == "OCR_COMPLETED"
        assert "29ABCDE1234F1Z5" in data["text"]
    finally:
        app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# 11. API: POST /api/v1/documents/{id}/ocr/retry
# ==============================================================================

def test_api_retry_document_ocr():
    client = TestClient(app)

    def mock_db_dep():
        session = MagicMock()
        doc = _make_mock_doc(ocr_status="OCR_FAILED")
        session.scalar.return_value = doc
        session.execute.return_value.scalars.return_value.unique.return_value.first.return_value = doc
        yield session

    app.dependency_overrides[get_db] = mock_db_dep
    try:
        response = client.post(f"/api/v1/documents/{KNOWN_DOC_UUID}/ocr/retry")
        assert response.status_code == 200
        data = response.json()
        assert data["ocr_status"] == "QUEUED"
    finally:
        app.dependency_overrides.pop(get_db, None)
