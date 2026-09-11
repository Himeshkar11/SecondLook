"""Backend tests for Bidder Details API endpoints and BidderService.get_bidder.

Tests cover:
1. GET /api/v1/bidders/{id} returns 200 for a known bidder (by UUID).
2. Returned bidder fields map correctly (name, pan, gstin, status, tenderId).
3. Nonexistent bidder UUID returns 404.
4. Non-UUID string ID returns 404 (not 422).
5. Database failure on GET /api/v1/bidders/{id} returns 500 safely without leaking internals.
6. Associated tender relationship is returned when bidder has linked tender.
7. Bidder with zero tenders returns gracefully without crashing (tenderId: None, tenders: []).
8. Bidder relationship is resolved dynamically from DB, not hardcoded.
9. Live integration test against real Supabase database.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db

# ─── Known IDs (match live seed data) ─────────────────────────────────────────

KNOWN_BIDDER_UUID = '00000000-0000-0000-0000-000000000021'
KNOWN_TENDER_UUID = '00000000-0000-0000-0000-000000000011'
KNOWN_TENDER_REF = 'GEM/2026/B/892104'


# ─── Mock factory helpers ──────────────────────────────────────────────────────

def _make_mock_tender():
    t = MagicMock()
    t.id = uuid.UUID(KNOWN_TENDER_UUID)
    t.reference_number = KNOWN_TENDER_REF
    t.title = 'CPCL Procurement Tender'
    t.status = 'ACTIVE'
    return t


def _make_mock_user():
    u = MagicMock()
    u.id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    u.email = 'vendor@abctech.com'
    u.full_name = 'ABC Tech Admin'
    return u


def _make_mock_bidder(with_tenders=True):
    """Return a mock Bidder ORM object."""
    b = MagicMock()
    b.id = uuid.UUID(KNOWN_BIDDER_UUID)
    b.user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    b.legal_name = 'ABC Technologies Pvt Ltd'
    b.pan_number = 'ABCDE1234F'
    b.gst_number = '27ABCDE1234F1Z5'
    b.registration_number = 'REG-ABC-2026'
    b.status = 'verified'
    b.created_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    b.updated_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    b.user = _make_mock_user()
    b.documents = []

    if with_tenders:
        b.tenders = [_make_mock_tender()]
    else:
        b.tenders = []

    return b


def _mock_session_for_bidder(bidder_obj):
    """Return a mock session that returns `bidder_obj` for any execute()."""
    session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.unique.return_value.first.return_value = bidder_obj
    result.scalars.return_value.first.return_value = bidder_obj
    session.execute.return_value = result
    session.scalar.return_value = 1 if bidder_obj else 0
    return session


def _mock_session_miss():
    """Return a mock session that returns None for execute."""
    session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.unique.return_value.first.return_value = None
    result.scalars.return_value.first.return_value = None
    session.execute.return_value = result
    session.scalar.return_value = 0
    return session


def _mock_session_fail():
    """Return a mock session that raises on any execute."""
    session = MagicMock()
    session.execute.side_effect = RuntimeError('Simulated database failure')
    session.scalar.side_effect = RuntimeError('Simulated database failure')
    return session


# ─── Test 1: GET /api/v1/bidders/{uuid} returns 200 ──────────────────────────

def test_get_bidder_by_uuid_returns_200():
    client = TestClient(app)

    def override():
        yield _mock_session_for_bidder(_make_mock_bidder())

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == KNOWN_BIDDER_UUID
        assert data['name'] == 'ABC Technologies Pvt Ltd'
        assert data['status'] == 'VERIFIED'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 2: Returned bidder fields map correctly ────────────────────────────

def test_get_bidder_fields_map_correctly():
    client = TestClient(app)

    def override():
        yield _mock_session_for_bidder(_make_mock_bidder())

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
        assert response.status_code == 200
        data = response.json()
        assert data['pan'] == 'ABCDE1234F'
        assert data['gstin'] == '27ABCDE1234F1Z5'
        assert data['gst_number'] == '27ABCDE1234F1Z5'
        assert data['registration_number'] == 'REG-ABC-2026'
        assert data['tenderId'] == KNOWN_TENDER_REF
        assert data['compliance'] == 94
        assert data['risk'] == 'LOW'
        assert 'registeredAddress' in data
        assert 'contactPerson' in data
        assert 'email' in data
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 3: Nonexistent UUID returns 404 ─────────────────────────────────────

def test_get_bidder_unknown_uuid_returns_404():
    client = TestClient(app)

    def override():
        yield _mock_session_miss()

    app.dependency_overrides[get_db] = override
    try:
        response = client.get('/api/v1/bidders/00000000-0000-0000-0000-000000000999')
        assert response.status_code == 404
        data = response.json()
        assert data['detail']['error']['code'] == 'RESOURCE_NOT_FOUND'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 4: Invalid non-UUID string returns 404 (not 422) ───────────────────

def test_get_bidder_invalid_string_id_returns_404():
    client = TestClient(app)

    def override():
        yield _mock_session_miss()

    app.dependency_overrides[get_db] = override
    try:
        response = client.get('/api/v1/bidders/nonexistent-id')
        assert response.status_code == 404
        data = response.json()
        assert data['detail']['error']['code'] == 'RESOURCE_NOT_FOUND'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 5: Database failure returns 500 safely ──────────────────────────────

def test_get_bidder_db_failure_returns_500():
    client = TestClient(app)

    def override():
        yield _mock_session_fail()

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data['detail']
        assert data['detail']['error']['code'] == 'DATABASE_ERROR'
        assert 'RuntimeError' not in str(data)
        assert 'Simulated' not in str(data)
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 6: Associated tender relationship is returned ───────────────────────

def test_get_bidder_returns_associated_tender():
    client = TestClient(app)

    def override():
        yield _mock_session_for_bidder(_make_mock_bidder(with_tenders=True))

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
        assert response.status_code == 200
        data = response.json()
        assert data['tenderId'] == KNOWN_TENDER_REF
        assert data['tender_id'] == KNOWN_TENDER_UUID
        assert len(data['tenders']) == 1
        assert data['tenders'][0]['reference_number'] == KNOWN_TENDER_REF
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 7: Bidder with zero tenders handled gracefully ─────────────────────

def test_get_bidder_handles_zero_tenders_gracefully():
    client = TestClient(app)

    def override():
        yield _mock_session_for_bidder(_make_mock_bidder(with_tenders=False))

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
        assert response.status_code == 200
        data = response.json()
        assert data['tenderId'] is None
        assert data['tenders'] == []
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 8: Data is dynamic from DB, not hardcoded ──────────────────────────

def test_bidder_data_is_dynamic_not_hardcoded():
    client = TestClient(app)

    custom_bidder = _make_mock_bidder()
    custom_bidder.legal_name = 'Dynamic Testing Bidder Corp'
    custom_bidder.pan_number = 'DYNMC9999Z'

    def override():
        yield _mock_session_for_bidder(custom_bidder)

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Dynamic Testing Bidder Corp'
        assert data['pan'] == 'DYNMC9999Z'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 9: Live integration against real Supabase ──────────────────────────

def test_get_bidder_live_returns_real_data():
    """Integration test against live Supabase — validates seeded bidder exists."""
    client = TestClient(app)
    response = client.get(f'/api/v1/bidders/{KNOWN_BIDDER_UUID}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == KNOWN_BIDDER_UUID
    assert 'ABC Technologies' in data['name']
    assert data['pan'] == 'ABCDE1234F'
    assert data['tenderId'] == KNOWN_TENDER_REF
    assert len(data['tenders']) >= 1
