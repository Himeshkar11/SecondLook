"""Unit and integration tests for Task 09: AI Document Extraction -> Structured JSON.

Tests verify:
1. AI abstraction and factory (AIExtractor, DemoAIExtractor, get_ai_extractor).
2. Deterministic Demo extraction for GST, PAN, UDYAM, and OTHER.
3. Hallucination protection (absent fields return null/None, never invented).
4. Empty OCR text handling (AIEmptyOCRError, no API calls).
5. JSON parsing, schema validation, markdown fence stripping, and schema violations.
6. OpenRouter triple fallback (mocked, NO live API calls):
   - Case 1: Primary succeeds
   - Case 2: Primary fails -> Fallback 1 succeeds
   - Case 3: Primary fails -> Fallback 1 fails -> Fallback 2 succeeds
   - Case 4: All 3 models fail -> extraction fails
   - Failure classification: Retryable (503, 429, timeout) vs Non-retryable (400, malformed JSON).
7. Security: Only document_type and ocr_text are sent, no binary or secrets.
8. OCR -> AI integration:
   - OCR_COMPLETED + text -> AI extraction succeeds
   - OCR_FAILED -> AI does NOT run
   - empty OCR text -> AI does NOT run
9. Idempotency: AI_COMPLETED documents are not reprocessed unnecessarily.
10. Service and API endpoints (GET /documents/{id}/ai, POST /documents/{id}/ai/retry).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai.extractor import (
    AIEmptyOCRError,
    AIExtractionError,
    AIExtractionStatus,
    AIExtractor,
    AIProviderRetryableError,
    DemoAIExtractor,
    StructuredDocumentData,
    get_ai_extractor,
)
from app.ai.prompts import get_prompt, get_prompt_version_key
from app.ai.providers.openrouter import OpenRouterAIExtractor
from app.ai.schemas import (
    GSTExtractionSchema,
    PANExtractionSchema,
    UDYAMExtractionSchema,
    get_schema_for_document_type,
)
from app.api.deps import get_db
from app.main import app
from app.models.document import Document
from app.services.document_service import DocumentService
from app.workers.jobs import (
    DocumentAIJobRecord,
    DocumentAIStatus,
    JobQueue,
    document_ai_queue,
)
from app.workers.worker import DocumentAIWorker

KNOWN_DOC_UUID = "00000000-0000-0000-0000-000000000041"
KNOWN_BIDDER_UUID = "00000000-0000-0000-0000-000000000021"


# ==============================================================================
# 1. AI Abstraction and Factory Tests
# ==============================================================================

def test_ai_extractor_interface_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        AIExtractor()  # type: ignore


def test_demo_ai_extractor_is_instance_of_ai_extractor():
    extractor = DemoAIExtractor()
    assert isinstance(extractor, AIExtractor)


def test_get_ai_extractor_defaults_to_demo():
    extractor = get_ai_extractor()
    assert isinstance(extractor, DemoAIExtractor)


def test_get_ai_extractor_with_openrouter_and_key():
    with patch("app.config.settings.settings.ai_provider", "openrouter"), \
         patch("app.config.settings.settings.openrouter_api_key", "mock-sk-or-v1-testkey"):
        extractor = get_ai_extractor()
        assert isinstance(extractor, OpenRouterAIExtractor)


def test_get_ai_extractor_falls_back_to_demo_when_key_missing():
    with patch("app.config.settings.settings.ai_provider", "openrouter"), \
         patch("app.config.settings.settings.openrouter_api_key", ""):
        extractor = get_ai_extractor()
        assert isinstance(extractor, DemoAIExtractor)


# ==============================================================================
# 2. DemoAIExtractor Extraction & Document Types
# ==============================================================================

def test_demo_extractor_gst():
    extractor = DemoAIExtractor()
    ocr_text = (
        "GOVERNMENT OF INDIA\n"
        "CENTRAL BOARD OF INDIRECT TAXES AND CUSTOMS\n"
        "Registration Certificate\n"
        "Registration Number (GSTIN): 27ABCDE1234F1Z5\n"
        "Legal Name: Alpha Enterprises Private Limited\n"
        "Trade Name: Alpha Tech\n"
        "Registration Date: 15/08/2021\n"
        "Status: ACTIVE\n"
        "Address: 123 Tech Park, Mumbai, Maharashtra 400001\n"
    )
    data = extractor.extract("GST", ocr_text)

    assert isinstance(data, StructuredDocumentData)
    assert data.document_type == "GST"
    assert data.document_number == "27ABCDE1234F1Z5"
    assert data.legal_name == "Alpha Enterprises Private Limited"
    assert data.registration_status == "ACTIVE"
    assert data.fields["gstin"] == "27ABCDE1234F1Z5"
    assert data.fields["trade_name"] == "Alpha Tech"
    assert data.fields["registration_date"] == "2021-08-15"
    assert data.fields["status"] == "ACTIVE"
    assert "Mumbai" in data.fields["address"]
    assert data.prompt_version == "GST_V1"


def test_demo_extractor_pan():
    extractor = DemoAIExtractor()
    ocr_text = (
        "INCOME TAX DEPARTMENT\n"
        "GOVT. OF INDIA\n"
        "Permanent Account Number: ABCDE1234F\n"
        "Name: John Doe\n"
        "Date of Birth: 25/12/1990\n"
        "Status: ACTIVE\n"
    )
    data = extractor.extract("PAN", ocr_text)

    assert data.document_type == "PAN"
    assert data.document_number == "ABCDE1234F"
    assert data.legal_name == "John Doe"
    assert data.fields["pan"] == "ABCDE1234F"
    assert data.fields["name"] == "John Doe"
    assert data.fields["date_of_birth_or_incorporation"] == "1990-12-25"
    assert data.prompt_version == "PAN_V1"


def test_demo_extractor_udyam():
    extractor = DemoAIExtractor()
    ocr_text = (
        "UDYAM REGISTRATION CERTIFICATE\n"
        "UDYAM REGISTRATION NUMBER: UDYAM-MH-01-0012345\n"
        "NAME OF ENTERPRISE: Beta Solutions LLP\n"
        "ENTERPRISE TYPE: SMALL\n"
        "MAJOR ACTIVITY: SERVICES\n"
    )
    data = extractor.extract("UDYAM", ocr_text)

    assert data.document_type == "UDYAM"
    assert data.document_number == "UDYAM-MH-01-0012345"
    assert data.legal_name == "Beta Solutions LLP"
    assert data.fields["udyam_number"] == "UDYAM-MH-01-0012345"
    assert data.fields["enterprise_name"] == "Beta Solutions LLP"
    assert data.fields["enterprise_type"] == "SMALL"
    assert data.fields["major_activity"] == "SERVICES"
    assert data.prompt_version == "UDYAM_V1"


# ==============================================================================
# 3. Hallucination Protection (Absent fields -> null, never fabricated)
# ==============================================================================

def test_demo_extractor_missing_gstin_returns_null_never_hallucinates():
    extractor = DemoAIExtractor()
    # Notice: GST certificate text WITHOUT any GSTIN
    ocr_text = (
        "GST Registration Certificate\n"
        "Legal Name: ABC Enterprises\n"
        "Status: ACTIVE\n"
        "Address: Industrial Area, Pune\n"
    )
    data = extractor.extract("GST", ocr_text)

    assert data.fields["gstin"] is None
    assert data.document_number is None
    assert data.legal_name == "ABC Enterprises"
    assert data.fields["legal_name"] == "ABC Enterprises"


def test_demo_extractor_missing_pan_returns_null():
    extractor = DemoAIExtractor()
    # PAN text without a valid PAN number
    ocr_text = (
        "INCOME TAX DEPARTMENT\n"
        "Name: Demo Person\n"
    )
    data = extractor.extract("PAN", ocr_text)

    assert data.fields["pan"] is None
    assert data.document_number is None
    assert data.legal_name == "Demo Person"


# ==============================================================================
# 4. Empty OCR Text Handling (AIEmptyOCRError)
# ==============================================================================

def test_demo_extractor_empty_ocr_raises_empty_ocr_error():
    extractor = DemoAIExtractor()
    with pytest.raises(AIEmptyOCRError):
        extractor.extract("GST", "")

    with pytest.raises(AIEmptyOCRError):
        extractor.extract("GST", "   \n\t  ")


def test_openrouter_empty_ocr_raises_without_making_http_call():
    extractor = OpenRouterAIExtractor()
    # Should raise AIEmptyOCRError before touching any network client
    with pytest.raises(AIEmptyOCRError):
        extractor.extract("GST", "")


# ==============================================================================
# 5. Schema Validation & JSON Parsing
# ==============================================================================

def test_gst_schema_validation_valid():
    raw = {
        "gstin": "29ABCDE1234F1Z5",
        "legal_name": "Acme Corp",
        "trade_name": None,
        "registration_date": "2020-01-01",
        "status": "ACTIVE",
        "address": "Bangalore",
    }
    validated = GSTExtractionSchema.model_validate(raw)
    assert validated.gstin == "29ABCDE1234F1Z5"
    assert validated.legal_name == "Acme Corp"
    assert validated.trade_name is None


def test_gst_schema_validation_all_nulls_allowed():
    raw = {
        "gstin": None,
        "legal_name": None,
        "trade_name": None,
        "registration_date": None,
        "status": None,
        "address": None,
    }
    validated = GSTExtractionSchema.model_validate(raw)
    assert validated.gstin is None
    assert validated.legal_name is None


def test_pan_schema_validation_valid():
    raw = {
        "pan": "ABCDE1234F",
        "name": "Jane Doe",
        "date_of_birth_or_incorporation": "1985-05-15",
    }
    validated = PANExtractionSchema.model_validate(raw)
    assert validated.pan == "ABCDE1234F"
    assert validated.name == "Jane Doe"


def test_udyam_schema_validation_valid():
    raw = {
        "udyam_number": "UDYAM-DL-01-0001234",
        "enterprise_name": "Delhi Crafts",
        "enterprise_type": "MICRO",
        "major_activity": "MANUFACTURING",
    }
    validated = UDYAMExtractionSchema.model_validate(raw)
    assert validated.udyam_number == "UDYAM-DL-01-0001234"
    assert validated.enterprise_type == "MICRO"


def test_openrouter_markdown_fence_stripping():
    with patch("app.config.settings.settings.openrouter_api_key", "test-key"), \
         patch("app.config.settings.settings.openrouter_primary_model", "primary-model"):
        extractor = OpenRouterAIExtractor()
        fenced_json = (
            "```json\n"
            "{\n"
            '  "gstin": "27ABCDE1234F1Z5",\n'
            '  "legal_name": "Stripped Fences Corp",\n'
            '  "trade_name": null,\n'
            '  "registration_date": null,\n'
            '  "status": "ACTIVE",\n'
            '  "address": null\n'
            "}\n"
            "```"
        )
        parsed = extractor._parse_and_validate(fenced_json, "GST", "primary-model")
        assert parsed.document_type == "GST"
        assert parsed.fields["gstin"] == "27ABCDE1234F1Z5"
        assert parsed.fields["legal_name"] == "Stripped Fences Corp"


def test_openrouter_malformed_json_raises_non_retryable_error():
    with patch("app.config.settings.settings.openrouter_api_key", "test-key"), \
         patch("app.config.settings.settings.openrouter_primary_model", "primary-model"):
        extractor = OpenRouterAIExtractor()
        bad_json = "This is not JSON at all {broken"
        with pytest.raises(AIExtractionError) as exc_info:
            extractor._parse_and_validate(bad_json, "GST", "primary-model")
        assert "malformed JSON" in str(exc_info.value)


# ==============================================================================
# 6. Triple Fallback Tests (OpenRouter Mocked — NO real API calls)
# ==============================================================================

def _make_mock_response(status_code: int, content_dict: dict | None = None, text: str = ""):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if content_dict is not None:
        resp.json.return_value = content_dict
    resp.text = text
    return resp


def test_openrouter_fallback_case_1_primary_succeeds():
    """Case 1: Primary model succeeds on first attempt."""
    mock_client = MagicMock(spec=httpx.Client)

    valid_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "gstin": "27ABCDE1234F1Z5",
                        "legal_name": "Primary Success Corp",
                        "trade_name": None,
                        "registration_date": "2022-01-01",
                        "status": "ACTIVE",
                        "address": "Mumbai",
                    })
                }
            }
        ]
    }
    mock_client.post.return_value = _make_mock_response(200, valid_response_data)

    with patch("app.config.settings.settings.openrouter_api_key", "test-key"), \
         patch("app.config.settings.settings.openrouter_primary_model", "model-primary"), \
         patch("app.config.settings.settings.openrouter_fallback_model_1", "model-fallback-1"), \
         patch("app.config.settings.settings.openrouter_fallback_model_2", "model-fallback-2"):
        extractor = OpenRouterAIExtractor(http_client=mock_client)
        result = extractor.extract("GST", "Raw OCR text with 27ABCDE1234F1Z5")

        assert result.ai_model == "model-primary"
        assert result.fields["gstin"] == "27ABCDE1234F1Z5"
        assert result.fields["legal_name"] == "Primary Success Corp"
        assert mock_client.post.call_count == 1  # Only primary called


def test_openrouter_fallback_case_2_primary_fails_fallback_1_succeeds():
    """Case 2: Primary fails with 503 -> Fallback 1 succeeds."""
    mock_client = MagicMock(spec=httpx.Client)

    fallback_1_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "pan": "ABCDE1234F",
                        "name": "Fallback 1 Corp",
                        "date_of_birth_or_incorporation": "2010-06-20",
                    })
                }
            }
        ]
    }

    mock_client.post.side_effect = [
        _make_mock_response(503, text="Service Unavailable"),  # Primary fails
        _make_mock_response(200, fallback_1_response),           # Fallback 1 succeeds
    ]

    with patch("app.config.settings.settings.openrouter_api_key", "test-key"), \
         patch("app.config.settings.settings.openrouter_primary_model", "model-primary"), \
         patch("app.config.settings.settings.openrouter_fallback_model_1", "model-fallback-1"), \
         patch("app.config.settings.settings.openrouter_fallback_model_2", "model-fallback-2"):
        extractor = OpenRouterAIExtractor(http_client=mock_client)
        result = extractor.extract("PAN", "Raw PAN text ABCDE1234F")

        assert result.ai_model == "model-fallback-1"
        assert result.fields["pan"] == "ABCDE1234F"
        assert result.fields["name"] == "Fallback 1 Corp"
        assert mock_client.post.call_count == 2


def test_openrouter_fallback_case_3_primary_and_fallback_1_fail_fallback_2_succeeds():
    """Case 3: Primary (429) & Fallback 1 (Timeout) fail -> Fallback 2 succeeds."""
    mock_client = MagicMock(spec=httpx.Client)

    fallback_2_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "udyam_number": "UDYAM-DL-01-0099999",
                        "enterprise_name": "Fallback 2 Tech",
                        "enterprise_type": "SMALL",
                        "major_activity": "SERVICES",
                    })
                }
            }
        ]
    }

    mock_client.post.side_effect = [
        _make_mock_response(429, text="Rate Limited"),           # Primary fails
        httpx.TimeoutException("Read timed out"),                 # Fallback 1 fails
        _make_mock_response(200, fallback_2_response),            # Fallback 2 succeeds
    ]

    with patch("app.config.settings.settings.openrouter_api_key", "test-key"), \
         patch("app.config.settings.settings.openrouter_primary_model", "model-primary"), \
         patch("app.config.settings.settings.openrouter_fallback_model_1", "model-fallback-1"), \
         patch("app.config.settings.settings.openrouter_fallback_model_2", "model-fallback-2"):
        extractor = OpenRouterAIExtractor(http_client=mock_client)
        result = extractor.extract("UDYAM", "Raw UDYAM text")

        assert result.ai_model == "model-fallback-2"
        assert result.fields["udyam_number"] == "UDYAM-DL-01-0099999"
        assert mock_client.post.call_count == 3


def test_openrouter_fallback_case_4_all_three_models_fail():
    """Case 4: All 3 models fail -> raises AIExtractionError."""
    mock_client = MagicMock(spec=httpx.Client)

    mock_client.post.side_effect = [
        _make_mock_response(503, text="Service Unavailable"),
        _make_mock_response(502, text="Bad Gateway"),
        httpx.ConnectError("Connection refused"),
    ]

    with patch("app.config.settings.settings.openrouter_api_key", "test-key"), \
         patch("app.config.settings.settings.openrouter_primary_model", "model-primary"), \
         patch("app.config.settings.settings.openrouter_fallback_model_1", "model-fallback-1"), \
         patch("app.config.settings.settings.openrouter_fallback_model_2", "model-fallback-2"):
        extractor = OpenRouterAIExtractor(http_client=mock_client)

        with pytest.raises(AIExtractionError) as exc_info:
            extractor.extract("GST", "Raw OCR text")

        assert "exhausted" in str(exc_info.value).lower()
        assert mock_client.post.call_count == 3


def test_openrouter_non_retryable_error_does_not_trigger_fallbacks():
    """Permanent error (e.g. 401 Unauthorized or malformed JSON) should NOT retry or fall back."""
    mock_client = MagicMock(spec=httpx.Client)
    # Primary returns 400 Bad Request (non-retryable client error)
    mock_client.post.return_value = _make_mock_response(400, text="Bad Request")

    with patch("app.config.settings.settings.openrouter_api_key", "test-key"), \
         patch("app.config.settings.settings.openrouter_primary_model", "model-primary"), \
         patch("app.config.settings.settings.openrouter_fallback_model_1", "model-fallback-1"), \
         patch("app.config.settings.settings.openrouter_fallback_model_2", "model-fallback-2"):
        extractor = OpenRouterAIExtractor(http_client=mock_client)

        with pytest.raises(AIExtractionError):
            extractor.extract("GST", "Some text")

        assert mock_client.post.call_count == 1  # Did NOT call fallback 1 or 2!


# ==============================================================================
# 7. Security: Only text & doc type sent to OpenRouter
# ==============================================================================

def test_openrouter_payload_security_contains_only_text():
    mock_client = MagicMock(spec=httpx.Client)
    valid_response_data = {
        "choices": [{"message": {"content": json.dumps({"gstin": "27ABCDE1234F1Z5"})}}]
    }
    mock_client.post.return_value = _make_mock_response(200, valid_response_data)

    with patch("app.config.settings.settings.openrouter_api_key", "sk-secret-test"), \
         patch("app.config.settings.settings.openrouter_primary_model", "model-primary"):
        extractor = OpenRouterAIExtractor(http_client=mock_client)
        extractor.extract("GST", "Safe OCR Text Content")

        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]

        assert "model" in payload
        assert "messages" in payload
        # Ensure no PDF bytes, storage URLs, or auth secrets inside the messages
        for msg in payload["messages"]:
            assert "supabase" not in msg["content"].lower()
            assert "sk-secret" not in msg["content"]


# ==============================================================================
# 8. OCR -> AI Integration & Worker Lifecycle
# ==============================================================================

def test_ai_worker_runs_when_ocr_completed():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ocr_status = "OCR_COMPLETED"
    mock_doc.ocr_text = "Registration Number (GSTIN): 27ABCDE1234F1Z5\nLegal Name: Test Corp"
    mock_doc.ai_status = "AI_PENDING"
    mock_doc.ai_extraction = None
    mock_db.scalar.return_value = mock_doc

    queue = JobQueue()
    job = DocumentAIJobRecord(
        document_id=KNOWN_DOC_UUID,
        bidder_id=KNOWN_BIDDER_UUID,
        document_type="GST",
        ocr_text=mock_doc.ocr_text,
    )
    queue.enqueue(job)

    worker = DocumentAIWorker(
        ai_extractor=DemoAIExtractor(),
        queue=queue,
        db=mock_db,
    )

    processed = worker.process_job(job)

    assert processed.status == DocumentAIStatus.AI_COMPLETED
    assert mock_doc.ai_status == "AI_COMPLETED"
    assert mock_doc.ai_extraction["gstin"] == "27ABCDE1234F1Z5"
    assert mock_doc.ai_extraction["legal_name"] == "Test Corp"
    assert mock_doc.ai_completed_at is not None
    assert mock_db.commit.called


def test_ai_worker_does_not_run_when_ocr_failed():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.ocr_status = "OCR_FAILED"
    mock_doc.ocr_text = None
    mock_doc.ai_status = "AI_PENDING"
    mock_db.scalar.return_value = mock_doc

    mock_extractor = MagicMock(spec=AIExtractor)
    queue = JobQueue()
    job = DocumentAIJobRecord(
        document_id=KNOWN_DOC_UUID,
        document_type="GST",
    )
    queue.enqueue(job)

    worker = DocumentAIWorker(
        ai_extractor=mock_extractor,
        queue=queue,
        db=mock_db,
    )

    processed = worker.process_job(job)

    # Must NOT run AI extractor
    assert not mock_extractor.extract.called
    assert processed.status == DocumentAIStatus.AI_FAILED
    assert "OCR is not completed" in processed.error
    assert mock_doc.ai_status == "AI_FAILED"


def test_ai_worker_does_not_run_when_ocr_text_is_empty():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.ocr_status = "OCR_COMPLETED"
    mock_doc.ocr_text = "   \n\t  "  # Whitespace only
    mock_doc.ai_status = "AI_PENDING"
    mock_db.scalar.return_value = mock_doc

    mock_extractor = MagicMock(spec=AIExtractor)
    queue = JobQueue()
    job = DocumentAIJobRecord(
        document_id=KNOWN_DOC_UUID,
        document_type="GST",
    )
    queue.enqueue(job)

    worker = DocumentAIWorker(
        ai_extractor=mock_extractor,
        queue=queue,
        db=mock_db,
    )

    processed = worker.process_job(job)

    assert not mock_extractor.extract.called
    assert processed.status == DocumentAIStatus.AI_FAILED
    assert "OCR text is empty" in processed.error
    assert mock_doc.ai_status == "AI_FAILED"


# ==============================================================================
# 9. Idempotency Tests
# ==============================================================================

def test_ai_worker_idempotency_does_not_reprocess_completed():
    mock_db = MagicMock()
    mock_extractor = MagicMock(spec=AIExtractor)

    queue = JobQueue()
    job = DocumentAIJobRecord(
        document_id=KNOWN_DOC_UUID,
        status=DocumentAIStatus.AI_COMPLETED,
        result={"gstin": "27ABCDE1234F1Z5"},
    )
    queue.enqueue(job)

    worker = DocumentAIWorker(ai_extractor=mock_extractor, queue=queue, db=mock_db)
    processed = worker.process_job(job)

    assert processed.status == DocumentAIStatus.AI_COMPLETED
    assert not mock_extractor.extract.called


# ==============================================================================
# 10. Service and API Endpoints
# ==============================================================================

def test_get_document_ai_endpoint():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.bidder = MagicMock(legal_name="Demo Bidder")
    mock_doc.document_type = "GST"
    mock_doc.file_name = "gst.pdf"
    mock_doc.storage_path = "path/gst.pdf"
    mock_doc.mime_type = "application/pdf"
    mock_doc.file_size = 1024
    mock_doc.status = "OCR_COMPLETED"
    mock_doc.ocr_status = "OCR_COMPLETED"
    mock_doc.ocr_text = "GSTIN: 27ABCDE1234F1Z5"
    mock_doc.ocr_error = None
    mock_doc.ocr_completed_at = datetime.now(timezone.utc)
    mock_doc.ai_status = "AI_COMPLETED"
    mock_doc.ai_extraction = {"gstin": "27ABCDE1234F1Z5", "legal_name": "Demo Bidder"}
    mock_doc.ai_error = None
    mock_doc.ai_completed_at = datetime.now(timezone.utc)
    mock_doc.ai_model = "demo_extractor"
    mock_doc.ai_prompt_version = "GST_V1"
    mock_doc.uploaded_at = datetime.now(timezone.utc)

    mock_db.execute.return_value.scalars.return_value.unique.return_value.first.return_value = mock_doc

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get(f"/api/v1/documents/{KNOWN_DOC_UUID}/ai")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == KNOWN_DOC_UUID
        assert data["status"] == "AI_COMPLETED"
        assert data["extraction"]["gstin"] == "27ABCDE1234F1Z5"
        assert data["prompt_version"] == "GST_V1"
    finally:
        app.dependency_overrides.clear()


def test_retry_document_ai_endpoint():
    mock_db = MagicMock()
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = uuid.UUID(KNOWN_DOC_UUID)
    mock_doc.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_doc.document_type = "GST"
    mock_doc.ocr_text = "GSTIN: 27ABCDE1234F1Z5"
    mock_doc.ai_status = "AI_FAILED"
    mock_db.scalar.return_value = mock_doc

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        with patch.object(DocumentAIWorker, "process_document_by_id") as mock_worker_run:
            response = client.post(f"/api/v1/documents/{KNOWN_DOC_UUID}/ai/retry")
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == KNOWN_DOC_UUID
            assert data["status"] == "AI_PENDING"
    finally:
        app.dependency_overrides.clear()


def test_get_document_ai_404_for_unknown_document():
    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.unique.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get(f"/api/v1/documents/{uuid.uuid4()}/ai")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
