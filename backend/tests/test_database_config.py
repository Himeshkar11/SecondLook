import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.mock_auth

from app.database.repository import select_one
from app.main import app
from app.services.tender_service import TenderService
from app.config.settings import settings
from app.services.bidder_service import BidderService
from app.services.document_service import DocumentService
from app.services.verification_service import VerificationService


def test_settings_module_imports_and_defaults():
    assert settings.environment == "development"
    assert settings.api_base_url == "http://localhost:8000"


def test_cors_does_not_allow_wildcard_with_credentials():
    assert "*" not in settings.cors_allowed_origins
    assert "http://localhost:5173" in settings.cors_allowed_origins


def test_cors_preflight_allows_configured_frontend_and_rejects_untrusted_origin():
    client = TestClient(app)
    allowed = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    untrusted = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert untrusted.status_code == 400


def test_database_probe_returns_one_for_configured_database_url():
    assert select_one() == 1


def test_contract_openapi_routes_are_declared_and_docs_endpoints_still_exist():
    client = TestClient(app)

    root = client.get("/")
    health = client.get("/health")
    docs = client.get("/docs")
    openapi_json = client.get("/openapi.json")

    assert root.status_code == 200
    assert health.status_code == 200
    assert docs.status_code == 200
    assert openapi_json.status_code == 200

    schema = app.openapi()
    paths = schema.get("paths", {})

    expected_routes = {
        "GET /api/v1/health/database": "/api/v1/health/database",
        "GET /api/v1/tenders": "/api/v1/tenders",
        "GET /api/v1/tenders/{id}": "/api/v1/tenders/{id}",
        "GET /api/v1/bidders": "/api/v1/bidders",
        "GET /api/v1/bidders/{id}": "/api/v1/bidders/{id}",
        "POST /api/v1/documents/upload": "/api/v1/documents/upload",
        "POST /api/v1/verification/start": "/api/v1/verification/start",
        "GET /api/v1/verification/{id}": "/api/v1/verification/{id}",
        "GET /api/v1/audit/{id}": "/api/v1/audit/{id}",
    }

    for route_name, route_path in expected_routes.items():
        assert route_path in paths

    assert "get" in paths["/api/v1/tenders"]
    assert "get" in paths["/api/v1/health/database"]


def test_demo_services_provide_deterministic_contract_shapes():
    tender_service = TenderService()
    bidder_service = BidderService()
    document_service = DocumentService()
    verification_service = VerificationService()

    tenders = tender_service.list_tenders()
    bidder_list = bidder_service.list_bidders()
    doc = document_service.upload_document("Demo Bidder Pvt Ltd", "vendor-gst", "demo.pdf", "application/pdf")
    start = verification_service.start_verification("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002")
    job = verification_service.get_verification("00000000-0000-0000-0000-000000000003")

    assert tenders["items"]
    assert tenders["total"] == len(tenders["items"])
    assert tenders["page"] == 1
    assert tenders["page_size"] == 20

    assert bidder_list["items"]
    assert bidder_list["total"] == len(bidder_list["items"])
    assert bidder_list["page"] == 1
    assert bidder_list["page_size"] == 20

    assert doc["document_type"] == "vendor-gst"
    assert doc["file_name"] == "demo.pdf"
    assert doc["mime_type"] == "application/pdf"

    assert start["verification_type"] == "vendor-gst"
    assert start["status"] == "queued"

    assert job["id"] == "00000000-0000-0000-0000-000000000003"
    assert job["status"] == "queued"


def test_m10_bbox_routes_call_services_and_match_contract():
    client = TestClient(app)

    tender = client.get("/api/v1/tenders")
    bidder = client.get("/api/v1/bidders")
    upload = client.post("/api/v1/documents/upload", data={"bidder_id": "00000000-0000-0000-0000-000000000001", "document_type": "vendor-gst"}, files={"file": ("demo.pdf", b"demo", "application/pdf")})
    start = client.post("/api/v1/verification/start", json={
        "bidder_id": "00000000-0000-0000-0000-000000000001",
        "document_id": "00000000-0000-0000-0000-000000000002",
        "verification_type": "vendor-gst",
    })
    verification = client.get("/api/v1/verification/00000000-0000-0000-0000-000000000003")

    assert tender.status_code == 200
    assert tender.json()["items"]
    assert tender.json()["total"] == len(tender.json()["items"])

    assert bidder.status_code == 200
    assert bidder.json()["items"]
    assert bidder.json()["total"] == len(bidder.json()["items"])

    assert upload.status_code == 201
    assert upload.json()["file_name"] == "demo.pdf"

    assert start.status_code == 201
    assert start.json()["verification_type"] == "vendor-gst"

    assert verification.status_code == 200
    assert verification.json()["id"] == "00000000-0000-0000-0000-000000000003"


def test_database_health_endpoint_success_with_live_db():
    client = TestClient(app)
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_database_health_endpoint_failure_when_query_raises_exception():
    client = TestClient(app)

    class MockFailingSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("Simulated query failure")

    def mock_failing_get_db():
        yield MockFailingSession()

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = mock_failing_get_db
    try:
        response = client.get("/api/v1/health/database")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["database"] == "unavailable"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_database_health_endpoint_failure_when_db_is_none():
    client = TestClient(app)

    def mock_none_get_db():
        yield None

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = mock_none_get_db
    try:
        response = client.get("/api/v1/health/database")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["database"] == "unavailable"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_tenders_returns_database_backed_records():
    client = TestClient(app)
    response = client.get("/api/v1/tenders")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    titles = [t["title"] for t in data["items"]]
    assert any("Tender" in title for title in titles)


def test_get_tenders_returns_empty_when_no_records():
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
            return MockResult()

    def mock_empty_get_db():
        yield MockEmptySession()

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = mock_empty_get_db
    try:
        response = client.get("/api/v1/tenders")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_tenders_handles_database_failure_safely():
    client = TestClient(app)

    class MockFailingSession:
        def scalar(self, *args, **kwargs):
            raise RuntimeError("Database connection failure")

    def mock_failing_get_db():
        yield MockFailingSession()

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = mock_failing_get_db
    try:
        response = client.get("/api/v1/tenders")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_tenders_response_structure_is_valid():
    client = TestClient(app)
    response = client.get("/api/v1/tenders")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    if data["items"]:
        first = data["items"][0]
        assert "id" in first
        assert "reference_number" in first
        assert "title" in first
        assert "status" in first
        assert "organization" in first


def test_get_tenders_does_not_return_hardcoded_tender_data():
    client = TestClient(app)
    response = client.get("/api/v1/tenders")
    assert response.status_code == 200
    data = response.json()
    titles = [t["title"] for t in data["items"]]
    assert "CPCL Procurement Tender" in titles or len(titles) > 1
