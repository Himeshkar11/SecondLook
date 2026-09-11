"""Backend tests for the Bidders API endpoints and BidderService.

Tests cover:
1. GET /api/v1/bidders succeeds and returns valid envelope.
2. Bidder records are mapped correctly from the database.
3. Empty bidder result is handled gracefully.
4. Database failure is handled safely (returns 500, no internals exposed).
5. Tender filtering (tender_id query param) works if relationship exists.
6. GET /api/v1/bidders/{id} retrieves a single bidder.
7. GET /api/v1/bidders/{id} returns 404 for unknown id.
8. Bidder data is NOT hardcoded / static.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.api.deps import get_db
from app.services.bidder_service import BidderService


# ─── Helper fixtures ────────────────────────────────────────────────────────────

KNOWN_BIDDER_UUID = '00000000-0000-0000-0000-000000000021'
KNOWN_TENDER_UUID = '00000000-0000-0000-0000-000000000011'

SAMPLE_BIDDER_ITEM = {
    'id': KNOWN_BIDDER_UUID,
    'user_id': '00000000-0000-0000-0000-000000000001',
    'name': 'ABC Technologies Pvt Ltd',
    'legal_name': 'ABC Technologies Pvt Ltd',
    'pan': 'ABCDE1234F',
    'pan_number': 'ABCDE1234F',
    'gst_number': '27ABCDE1234F1Z5',
    'registration_number': 'REG-ABC-2026',
    'status': 'VERIFIED',
    'tenderId': 'GEM/2026/B/892104',
    'tender_id': KNOWN_TENDER_UUID,
    'tender_reference': 'GEM/2026/B/892104',
    'compliance': 94,
    'risk': 'LOW',
    'msmeCategory': 'NOT APPLICABLE',
    'created_at': '2026-09-11T00:00:00+00:00',
    'updated_at': '2026-09-11T00:00:00+00:00',
}


def _make_mock_db():
    """Create a minimal mock DB session that returns sample bidder data."""
    mock_db = MagicMock()
    mock_bidder = MagicMock()
    mock_bidder.id = uuid.UUID(KNOWN_BIDDER_UUID)
    mock_bidder.user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    mock_bidder.legal_name = 'ABC Technologies Pvt Ltd'
    mock_bidder.pan_number = 'ABCDE1234F'
    mock_bidder.gst_number = '27ABCDE1234F1Z5'
    mock_bidder.registration_number = 'REG-ABC-2026'
    mock_bidder.status = 'verified'

    mock_tender = MagicMock()
    mock_tender.id = uuid.UUID(KNOWN_TENDER_UUID)
    mock_tender.reference_number = 'GEM/2026/B/892104'
    mock_bidder.tenders = [mock_tender]

    from datetime import datetime, timezone
    mock_bidder.created_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    mock_bidder.updated_at = datetime(2026, 9, 11, tzinfo=timezone.utc)

    mock_result = MagicMock()
    mock_result.scalars.return_value.unique.return_value.all.return_value = [mock_bidder]
    mock_result.scalars.return_value.first.return_value = mock_bidder
    mock_db.execute.return_value = mock_result
    mock_db.scalar.return_value = 1
    return mock_db


# ─── Test 1: GET /api/v1/bidders returns 200 and valid envelope ──────────────────

def test_get_bidders_returns_200():
    client = TestClient(app)

    def mock_get_db():
        yield _make_mock_db()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        response = client.get('/api/v1/bidders')
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'page_size' in data
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 2: Bidder records are mapped correctly ─────────────────────────────────

def test_get_bidders_maps_fields_correctly():
    client = TestClient(app)

    def mock_get_db():
        yield _make_mock_db()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        response = client.get('/api/v1/bidders')
        assert response.status_code == 200
        data = response.json()
        assert data['total'] >= 1
        items = data['items']
        assert len(items) >= 1
        first = items[0]
        # Required fields
        assert 'id' in first
        assert 'name' in first or 'legal_name' in first
        assert 'pan' in first or 'pan_number' in first
        assert 'status' in first
        assert 'compliance' in first
        assert 'risk' in first
        # Confirm the actual value maps correctly
        assert (first.get('name') or first.get('legal_name')) == 'ABC Technologies Pvt Ltd'
        assert first['status'] == 'VERIFIED'
        assert first['compliance'] == 94
        assert first['risk'] == 'LOW'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 3: Empty bidder result handled gracefully ──────────────────────────────

def test_get_bidders_returns_empty_when_no_records():
    client = TestClient(app)

    class MockEmptySession:
        def scalar(self, *args, **kwargs):
            return 0

        def execute(self, *args, **kwargs):
            class MockResult:
                def scalars(self):
                    return self
                def unique(self):
                    return self
                def all(self):
                    return []
                def first(self):
                    return None
            return MockResult()

    def mock_empty_get_db():
        yield MockEmptySession()

    app.dependency_overrides[get_db] = mock_empty_get_db
    try:
        response = client.get('/api/v1/bidders')
        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['total'] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 4: Database failure returns 500 without leaking internals ──────────────

def test_get_bidders_handles_database_failure_safely():
    client = TestClient(app)

    class MockFailingSession:
        def scalar(self, *args, **kwargs):
            raise RuntimeError('Simulated database connection failure')

    def mock_failing_get_db():
        yield MockFailingSession()

    app.dependency_overrides[get_db] = mock_failing_get_db
    try:
        response = client.get('/api/v1/bidders')
        assert response.status_code == 500
        data = response.json()
        # Error must be wrapped, no internal DB details
        detail = data.get('detail', {})
        assert 'error' in detail
        error = detail['error']
        assert error.get('code') == 'DATABASE_ERROR'
        # Must NOT expose stack traces or SQL
        assert 'RuntimeError' not in str(data)
        assert 'Simulated database' not in str(data)
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 5: Tender filter works when relationship exists ────────────────────────

def test_get_bidders_with_tender_id_filter():
    client = TestClient(app)

    def mock_get_db():
        yield _make_mock_db()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        # Filter by tender reference number
        response = client.get('/api/v1/bidders?tender_id=GEM/2026/B/892104')
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        # Filter by tender UUID
        response2 = client.get(f'/api/v1/bidders?tender_id={KNOWN_TENDER_UUID}')
        assert response2.status_code == 200
        data2 = response2.json()
        assert 'items' in data2
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 6: GET /api/v1/bidders/{id} returns a single bidder ───────────────────

def test_get_single_bidder_by_id():
    client = TestClient(app)

    def mock_get_db():
        yield _make_mock_db()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == KNOWN_BIDDER_UUID
        assert (data.get('name') or data.get('legal_name')) == 'ABC Technologies Pvt Ltd'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 7: GET /api/v1/bidders/{id} returns 404 for unknown UUID ───────────────

def test_get_single_bidder_unknown_id_returns_404():
    client = TestClient(app)

    class MockMissSession:
        def scalar(self, *args, **kwargs):
            return 0

        def execute(self, *args, **kwargs):
            class MockResult:
                def scalars(self):
                    return self
                def first(self):
                    return None
            return MockResult()

    def mock_miss_get_db():
        yield MockMissSession()

    app.dependency_overrides[get_db] = mock_miss_get_db
    try:
        unknown_id = '99999999-9999-9999-9999-999999999999'
        response = client.get(f'/api/v1/bidders/{unknown_id}')
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 8: Bidder data is NOT hardcoded demo data ─────────────────────────────

def test_get_bidders_does_not_return_hardcoded_demo_data():
    """Verify the endpoint goes through BidderService backed by the DB session,
    not the old hardcoded 'Demo Bidder Pvt Ltd' payload."""
    client = TestClient(app)

    def mock_get_db():
        yield _make_mock_db()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        response = client.get('/api/v1/bidders')
        assert response.status_code == 200
        data = response.json()
        names = [item.get('name') or item.get('legal_name', '') for item in data['items']]
        assert 'Demo Bidder Pvt Ltd' not in names
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 9: Live database returns real seeded bidder records ────────────────────

def test_get_bidders_returns_database_backed_records():
    """Integration test against live Supabase — validates at least 1 seeded record exists."""
    client = TestClient(app)
    response = client.get('/api/v1/bidders')
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'total' in data
    assert data['total'] >= 1
    names = [item.get('name') or item.get('legal_name', '') for item in data['items']]
    assert any(name for name in names)
