import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient

from app.config.settings import settings
from app.database.repository import select_one
from app.main import app
from app.services.tender_service import TenderService
from app.services.bidder_service import BidderService
from app.services.document_service import DocumentService
from app.services.verification_service import VerificationService


def test_settings_module_imports_and_defaults():
    assert settings.environment == "development"
    assert settings.api_base_url == "http://localhost:8000"


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
        "GET /api/v1/tenders": "/api/v1/tenders",
        "GET /api/v1/tenders/{id}": "/api/v1/tenders/{id}",
        "GET /api/v1/bidders": "/api/v1/bidders",
        "GET /api/v1/bidders/{id}": "/api/v1/bidders/{id}",
        "POST /api/v1/documents/upload": "/api/v1/documents/upload",
        "POST /api/v1/verification/start": "/api/v1/verification/start",
        "GET /api/v1/verification/{id}": "/api/v1/verification/{id}",
        "GET /api/v1/dashboard/summary": "/api/v1/dashboard/summary",
        "GET /api/v1/audit/{id}": "/api/v1/audit/{id}",
    }

    for route_name, route_path in expected_routes.items():
        assert route_path in paths

    assert "get" in paths["/api/v1/tenders"]


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
