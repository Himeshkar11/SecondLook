"""Backend tests for Tender Details API endpoints and TenderService.get_tender_bidders.

Tests cover:
1. GET /api/v1/tenders/{id} returns 200 for a known tender (by UUID).
2. GET /api/v1/tenders/{id} returns 200 for a known tender (by reference number).
3. GET /api/v1/tenders/{unknown_id} returns 404.
4. Database failure on GET /api/v1/tenders/{id} returns 500 safely.
5. GET /api/v1/tenders/{id}/bidders returns associated bidders.
6. Tender with zero bidders returns empty list from /bidders endpoint.
7. Bidder/tender relationship resolved from DB, not hardcoded.
8. GET /api/v1/tenders/{id}/bidders on unknown tender returns empty, not error.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from urllib.parse import quote
from fastapi.testclient import TestClient

pytestmark = pytest.mark.mock_auth

from app.main import app
from app.api.deps import get_db

# ─── Known IDs (match live seed data) ─────────────────────────────────────────

KNOWN_TENDER_UUID = '00000000-0000-0000-0000-000000000011'
KNOWN_TENDER_REF = 'GEM/2026/B/892104'
KNOWN_BIDDER_UUID = '00000000-0000-0000-0000-000000000021'


# ─── Mock factory helpers ──────────────────────────────────────────────────────

def _make_mock_creator():
    creator = MagicMock()
    creator.full_name = 'CPCL / Ministry of Petroleum'
    return creator


def _make_mock_tender(with_bidders=True):
    """Return a mock Tender ORM object."""
    t = MagicMock()
    t.id = uuid.UUID(KNOWN_TENDER_UUID)
    t.reference_number = KNOWN_TENDER_REF
    t.title = 'CPCL Procurement Tender — UPDATED'
    t.description = 'Procurement of enterprise networking equipment.'
    t.status = 'ACTIVE'
    t.created_by = uuid.UUID('00000000-0000-0000-0000-000000000001')
    t.created_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    t.updated_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    t.creator = _make_mock_creator()

    if with_bidders:
        b = MagicMock()
        b.id = uuid.UUID(KNOWN_BIDDER_UUID)
        b.legal_name = 'ABC Technologies Pvt Ltd'
        b.pan_number = 'ABCDE1234F'
        b.gst_number = '27ABCDE1234F1Z5'
        b.registration_number = 'REG-ABC-2026'
        b.status = 'verified'
        b.created_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
        b.updated_at = datetime(2026, 9, 11, tzinfo=timezone.utc)
        t.bidders = [b]
    else:
        t.bidders = []

    return t


def _mock_session_for_tender(tender_obj):
    """Return a mock session that returns `tender_obj` for any execute()."""
    session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.unique.return_value.all.return_value = [tender_obj] if tender_obj else []
    result.scalars.return_value.first.return_value = tender_obj
    session.execute.return_value = result
    session.scalar.return_value = 1 if tender_obj else 0
    return session


def _mock_session_miss():
    """Return a mock session that returns None for any single-record execute."""
    session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.unique.return_value.all.return_value = []
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


# ─── Test 1: GET /api/v1/tenders/{uuid} returns 200 ──────────────────────────

def test_get_tender_by_uuid_returns_200():
    client = TestClient(app)

    def override():
        yield _mock_session_for_tender(_make_mock_tender())

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == KNOWN_TENDER_UUID
        assert data['title'] == 'CPCL Procurement Tender — UPDATED'
        assert data['status'] == 'ACTIVE'
        assert 'reference_number' in data
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 2: GET /api/v1/tenders/{ref_number} returns 200 ────────────────────

def test_get_tender_by_reference_number_returns_200():
    client = TestClient(app)

    def override():
        yield _mock_session_for_tender(_make_mock_tender())

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/tenders/{quote(KNOWN_TENDER_REF, safe="")}')
        assert response.status_code == 200
        data = response.json()
        assert data['reference_number'] == KNOWN_TENDER_REF
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 3: Unknown tender ID returns 404 ────────────────────────────────────

def test_get_tender_unknown_id_returns_404():
    client = TestClient(app)

    def override():
        yield _mock_session_miss()

    app.dependency_overrides[get_db] = override
    try:
        response = client.get('/api/v1/tenders/NONEXISTENT-REF-9999')
        assert response.status_code == 404
        data = response.json()
        assert data['detail']['error']['code'] == 'RESOURCE_NOT_FOUND'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 4: Database failure returns 500 without leaking internals ───────────

def test_get_tender_db_failure_returns_500():
    client = TestClient(app)

    def override():
        yield _mock_session_fail()

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}')
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data['detail']
        assert data['detail']['error']['code'] == 'DATABASE_ERROR'
        assert 'RuntimeError' not in str(data)
        assert 'Simulated' not in str(data)
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 5: GET /api/v1/tenders/{id}/bidders returns associated bidders ──────

def test_get_tender_bidders_returns_associated_bidders():
    client = TestClient(app)

    def override():
        yield _mock_session_for_tender(_make_mock_tender(with_bidders=True))

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}/bidders')
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert data['total'] >= 1
        first = data['items'][0]
        assert first['id'] == KNOWN_BIDDER_UUID
        assert first['name'] == 'ABC Technologies Pvt Ltd'
        assert first['status'] == 'VERIFIED'
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 6: Tender with zero bidders returns empty list ──────────────────────

def test_get_tender_bidders_returns_empty_for_no_bidders():
    client = TestClient(app)

    def override():
        yield _mock_session_for_tender(_make_mock_tender(with_bidders=False))

    app.dependency_overrides[get_db] = override
    try:
        response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}/bidders')
        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['total'] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 7: Relationship resolved from DB, not hardcoded ────────────────────

def test_bidder_relationship_not_hardcoded():
    """Verify bidder list changes dynamically based on DB content."""
    client = TestClient(app)

    # Return a tender with NO bidders
    def override_empty():
        yield _mock_session_for_tender(_make_mock_tender(with_bidders=False))

    app.dependency_overrides[get_db] = override_empty
    try:
        response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}/bidders')
        assert response.json()['total'] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)

    # Now return the same tender WITH a bidder
    def override_with_bidder():
        yield _mock_session_for_tender(_make_mock_tender(with_bidders=True))

    app.dependency_overrides[get_db] = override_with_bidder
    try:
        response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}/bidders')
        assert response.json()['total'] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 8: Unknown tender returns empty bidder list (not error) ─────────────

def test_get_tender_bidders_unknown_tender_returns_empty():
    client = TestClient(app)

    def override():
        yield _mock_session_miss()

    app.dependency_overrides[get_db] = override
    try:
        response = client.get('/api/v1/tenders/NONEXISTENT-REF-9999/bidders')
        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['total'] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


# ─── Test 9: Live integration — real Supabase data ───────────────────────────

def test_get_tender_live_returns_real_data():
    """Integration test against live Supabase — validates a seeded tender exists."""
    client = TestClient(app)
    response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == KNOWN_TENDER_UUID
    assert data['reference_number'] == KNOWN_TENDER_REF
    assert 'title' in data
    assert 'status' in data


def test_get_tender_bidders_live_returns_real_data():
    """Integration test against live Supabase — validates bidder relationship."""
    client = TestClient(app)
    response = client.get(f'/api/v1/tenders/{KNOWN_TENDER_UUID}/bidders')
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'total' in data
    # ABC Technologies should be linked to this tender
    assert data['total'] >= 1
    names = [item.get('name', '') for item in data['items']]
    assert any('ABC Technologies' in n for n in names)
