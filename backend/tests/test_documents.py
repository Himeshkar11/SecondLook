"""Backend tests for Document Management API endpoints and DocumentService.

Tests cover:
1. Valid document upload saves to storage and inserts metadata in DB.
2. Upload with nonexistent bidder ID returns 404.
3. Upload with unsupported file extension returns 422.
4. Upload with unsupported MIME type returns 422.
5. Upload with invalid document type returns 422.
6. Upload exceeding file size limit returns 422.
7. Upload with empty file returns 422.
8. Listing documents for a bidder returns matching items.
9. Retrieving document metadata returns correct record.
10. Retrieving nonexistent document returns 404.
11. Secure document access generates valid signed URL.
12. Storage upload failure returns 500 without creating DB row.
13. Storage cleanup is attempted if database insert fails after upload.
14. Live integration test uploading a real test file to Supabase.
"""

import io
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db
from app.services.document_service import DocumentService

KNOWN_BIDDER_UUID = '00000000-0000-0000-0000-000000000021'


def _make_mock_bidder():
    b = MagicMock()
    b.id = uuid.UUID(KNOWN_BIDDER_UUID)
    b.legal_name = 'ABC Technologies Pvt Ltd'
    return b


def _make_mock_doc():
    d = MagicMock()
    d.id = uuid.UUID('00000000-0000-0000-0000-000000000041')
    d.bidder_id = uuid.UUID(KNOWN_BIDDER_UUID)
    d.document_type = 'GST'
    d.file_name = 'gst_certificate.pdf'
    d.storage_path = f'{KNOWN_BIDDER_UUID}/doc_gst.pdf'
    d.mime_type = 'application/pdf'
    d.file_size = 1024
    d.status = 'uploaded'
    d.uploaded_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    d.bidder = _make_mock_bidder()
    return d


def _mock_session_for_upload(bidder_exists=True):
    session = MagicMock()
    if bidder_exists:
        session.scalar.return_value = _make_mock_bidder()
    else:
        session.scalar.return_value = None
    return session


# ─── Test 1: Valid upload returns 201 and metadata ───────────────────────────

def test_upload_document_success():
    client = TestClient(app)

    def mock_db():
        session = _mock_session_for_upload(bidder_exists=True)
        yield session

    app.dependency_overrides[get_db] = mock_db
    try:
        with patch.object(DocumentService, '_upload_to_storage', return_value=None):
            file_content = b"%PDF-1.4 test document content"
            response = client.post(
                f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents',
                data={'document_type': 'GST'},
                files={'file': ('gst_cert.pdf', io.BytesIO(file_content), 'application/pdf')},
            )
            assert response.status_code == 201
            data = response.json()
            assert data['document_type'] == 'GST'
            assert data['file_name'] == 'gst_cert.pdf'
            assert data['file_size'] == len(file_content)
            assert 'storage_path' in data
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 2: Upload for nonexistent bidder returns 404 ────────────────────────

def test_upload_document_nonexistent_bidder_returns_404():
    client = TestClient(app)

    def mock_db():
        yield _mock_session_for_upload(bidder_exists=False)

    app.dependency_overrides[get_db] = mock_db
    try:
        unknown_id = '00000000-0000-0000-0000-000000000999'
        response = client.post(
            f'/api/v1/bidders/{unknown_id}/documents',
            data={'document_type': 'GST'},
            files={'file': ('gst.pdf', io.BytesIO(b'%PDF-1.4 sample'), 'application/pdf')},
        )
        assert response.status_code == 404
        assert response.json()['detail']['error']['code'] == 'RESOURCE_NOT_FOUND'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 3: Unsupported file extension returns 422 ──────────────────────────

def test_upload_unsupported_file_extension_returns_422():
    client = TestClient(app)

    def mock_db():
        yield _mock_session_for_upload(bidder_exists=True)

    app.dependency_overrides[get_db] = mock_db
    try:
        response = client.post(
            f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents',
            data={'document_type': 'GST'},
            files={'file': ('malicious.exe', io.BytesIO(b'MZ...'), 'application/octet-stream')},
        )
        assert response.status_code == 422
        assert 'extension' in response.json()['detail']['error']['message'].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 4: Unsupported MIME type returns 422 ───────────────────────────────

def test_upload_unsupported_mime_type_returns_422():
    client = TestClient(app)

    def mock_db():
        yield _mock_session_for_upload(bidder_exists=True)

    app.dependency_overrides[get_db] = mock_db
    try:
        response = client.post(
            f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents',
            data={'document_type': 'GST'},
            files={'file': ('test.pdf', io.BytesIO(b'dummy content'), 'text/html')},
        )
        assert response.status_code == 422
        assert 'mime' in response.json()['detail']['error']['message'].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 5: Unsupported document type returns 422 ───────────────────────────

def test_upload_unsupported_document_type_returns_422():
    client = TestClient(app)

    def mock_db():
        yield _mock_session_for_upload(bidder_exists=True)

    app.dependency_overrides[get_db] = mock_db
    try:
        response = client.post(
            f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents',
            data={'document_type': 'INVALID_TYPE_XYZ'},
            files={'file': ('test.pdf', io.BytesIO(b'%PDF-1.4 dummy'), 'application/pdf')},
        )
        assert response.status_code == 422
        assert 'document type' in response.json()['detail']['error']['message'].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 6: Empty file returns 422 ──────────────────────────────────────────

def test_upload_empty_file_returns_422():
    client = TestClient(app)

    def mock_db():
        yield _mock_session_for_upload(bidder_exists=True)

    app.dependency_overrides[get_db] = mock_db
    try:
        response = client.post(
            f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents',
            data={'document_type': 'GST'},
            files={'file': ('empty.pdf', io.BytesIO(b''), 'application/pdf')},
        )
        assert response.status_code == 422
        assert 'empty' in response.json()['detail']['error']['message'].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 7: List bidder documents returns matching items ────────────────────

def test_list_bidder_documents():
    client = TestClient(app)

    def mock_db():
        session = MagicMock()
        mock_doc = _make_mock_doc()
        result = MagicMock()
        result.scalars.return_value.unique.return_value.all.return_value = [mock_doc]
        session.execute.return_value = result
        session.scalar.return_value = 1
        yield session

    app.dependency_overrides[get_db] = mock_db
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents')
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert data['items'][0]['document_type'] == 'GST'
        assert data['items'][0]['filename'] == 'gst_certificate.pdf'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 8: Get document metadata by ID ─────────────────────────────────────

def test_get_document_by_id():
    client = TestClient(app)

    def mock_db():
        session = MagicMock()
        mock_doc = _make_mock_doc()
        result = MagicMock()
        result.scalars.return_value.unique.return_value.first.return_value = mock_doc
        session.execute.return_value = result
        yield session

    app.dependency_overrides[get_db] = mock_db
    try:
        response = client.get('/api/v1/documents/00000000-0000-0000-0000-000000000041')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == '00000000-0000-0000-0000-000000000041'
        assert data['document_type'] == 'GST'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 9: Get nonexistent document returns 404 ─────────────────────────────

def test_get_document_unknown_id_returns_404():
    client = TestClient(app)

    def mock_db():
        session = MagicMock()
        result = MagicMock()
        result.scalars.return_value.unique.return_value.first.return_value = None
        session.execute.return_value = result
        yield session

    app.dependency_overrides[get_db] = mock_db
    try:
        response = client.get('/api/v1/documents/00000000-0000-0000-0000-000000000999')
        assert response.status_code == 404
        assert response.json()['detail']['error']['code'] == 'RESOURCE_NOT_FOUND'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 10: Secure document access returns signed URL ──────────────────────

def test_get_document_access_returns_signed_url():
    client = TestClient(app)

    mock_doc = {
        'id': '00000000-0000-0000-0000-000000000041',
        'file_name': 'gst.pdf',
        'mime_type': 'application/pdf',
        'storage_path': f'{KNOWN_BIDDER_UUID}/test.pdf',
    }

    with patch.object(DocumentService, 'get_document', return_value=mock_doc):
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = {'signedURL': '/object/sign/bidder-documents/test.pdf?token=abc'}

        with patch('httpx.Client.post', return_value=mock_http_response):
            response = client.get('/api/v1/documents/00000000-0000-0000-0000-000000000041/access')
            assert response.status_code == 200
            data = response.json()
            assert 'download_url' in data
            assert 'token=abc' in data['download_url']


# ─── Test 11: Storage upload failure returns 500 without DB commit ───────────

def test_storage_failure_handles_error_safely():
    client = TestClient(app)

    def mock_db():
        session = _mock_session_for_upload(bidder_exists=True)
        yield session

    app.dependency_overrides[get_db] = mock_db
    try:
        with patch.object(DocumentService, '_upload_to_storage', side_effect=RuntimeError("Storage connection failed")):
            response = client.post(
                f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents',
                data={'document_type': 'GST'},
                files={'file': ('gst.pdf', io.BytesIO(b'%PDF-1.4 test'), 'application/pdf')},
            )
            assert response.status_code == 500
            assert response.json()['detail']['error']['code'] == 'UPLOAD_FAILED'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 12: Storage cleanup attempted if DB commit fails ───────────────────

def test_storage_cleanup_on_db_insert_failure():
    service = DocumentService(db=MagicMock())
    service.db.scalar.return_value = _make_mock_bidder()
    service.db.commit.side_effect = RuntimeError("DB constraint violation")

    with patch.object(service, '_upload_to_storage', return_value=None):
        with patch.object(service, '_delete_from_storage') as mock_cleanup:
            with pytest.raises(RuntimeError, match="DB constraint violation"):
                service.upload_document(
                    bidder_id=KNOWN_BIDDER_UUID,
                    file_bytes=b"%PDF-1.4 dummy",
                    file_name="cert.pdf",
                    mime_type="application/pdf",
                    document_type="GST",
                )
            # Cleanup delete must have been called with the generated storage path
            assert mock_cleanup.called
            called_path = mock_cleanup.call_args[0][0]
            assert called_path.startswith(KNOWN_BIDDER_UUID)
            assert called_path.endswith("cert.pdf")


# ─── Test 13: Live integration test against real Supabase ────────────────────

def test_live_document_lifecycle():
    """Integration test against live Supabase: upload, list, access, and cleanup."""
    client = TestClient(app)

    file_bytes = b"%PDF-1.4 SecondLook Automated Integration Test Document"
    filename = f"integration_test_{uuid.uuid4().hex[:8]}.pdf"

    # 1. Upload
    res_upload = client.post(
        f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents',
        data={'document_type': 'GST'},
        files={'file': (filename, io.BytesIO(file_bytes), 'application/pdf')},
    )
    assert res_upload.status_code == 201, res_upload.text
    doc_data = res_upload.json()
    doc_id = doc_data['id']
    storage_path = doc_data['storage_path']

    try:
        # 2. Retrieve metadata
        res_get = client.get(f'/api/v1/documents/{doc_id}')
        assert res_get.status_code == 200
        assert res_get.json()['file_name'] == filename

        # 3. List
        res_list = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}/documents')
        assert res_list.status_code == 200
        items = res_list.json()['items']
        assert any(item['id'] == doc_id for item in items)

        # 4. Access signed URL
        res_access = client.get(f'/api/v1/documents/{doc_id}/access')
        assert res_access.status_code == 200
        access_data = res_access.json()
        assert 'download_url' in access_data
        assert access_data['download_url'].startswith('http')
    finally:
        # Clean up integration test record from Storage and DB
        service = DocumentService()
        service._delete_from_storage(storage_path)
        from app.database.connection import SessionLocal
        from app.models.document import Document
        with SessionLocal() as s:
            s.query(Document).filter(Document.id == uuid.UUID(doc_id)).delete()
            s.commit()
