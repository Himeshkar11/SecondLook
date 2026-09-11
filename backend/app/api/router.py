"""Versioned FastAPI router for the M09/M10 contract and service boundary.

This router keeps the established API version prefix `/api/v1` and declares
contract-only endpoints for OpenAPI generation. The resource endpoints are
wired to deterministic demo service classes. They do not contain database
queries, CRUD, auth, or verification provider calls.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_api_request_context, get_db
from app.services.bidder_service import BidderService
from app.services.document_service import DocumentService
from app.services.tender_service import TenderService
from app.services.verification_service import VerificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.get("/health/database", tags=["Health"], summary="Database health check", responses={
    200: {"description": "Database connection healthy."},
    503: {"description": "Database connection unavailable."},
})
def health_database(db: Session = Depends(get_db)):
    """Perform a lightweight real read against the Supabase PostgreSQL database."""
    if db is None:
        logger.error("Database session is not available; DATABASE_URL may be missing.")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )

    try:
        db.execute(text("SELECT count(*) FROM demo_government_records")).scalar()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.error("Database health check query failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )


@router.get("/tenders", tags=["Tenders"], summary="List tenders", responses={
    200: {"description": "Paginated tender list response."},
    500: {"description": "Database query error."}
})
def list_tenders(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    """Route wrapper for TenderService.list_tenders."""
    service = TenderService(db=db)
    try:
        return service.list_tenders(page=page, page_size=page_size)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load tenders", "details": {}}},
        ) from exc


@router.get("/tenders/{id:path}/bidders", tags=["Tenders"], summary="Get bidders for a tender", responses={
    200: {"description": "List of bidders associated with the tender."},
    404: {"description": "Tender not found."},
    500: {"description": "Database query error."}
})
def get_tender_bidders(id: str, db: Session = Depends(get_db)):
    """Route wrapper for TenderService.get_tender_bidders."""
    service = TenderService(db=db)
    try:
        bidders = service.get_tender_bidders(id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load bidders for tender", "details": {}}},
        ) from exc
    return {"items": bidders, "total": len(bidders)}


@router.get("/tenders/{id:path}", tags=["Tenders"], summary="Get one tender", responses={
    200: {"description": "Tender response."},
    404: {"description": "Tender not found."},
    500: {"description": "Database query error."}
})
def get_tender(id: str, db: Session = Depends(get_db)):
    """Route wrapper for TenderService.get_tender. Accepts UUID or reference number."""
    service = TenderService(db=db)
    try:
        tender = service.get_tender(id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load tender details", "details": {}}},
        ) from exc
    if tender is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Tender not found", "details": {}}})
    return tender


@router.get("/bidders", tags=["Bidders"], summary="List bidders", responses={
    200: {"description": "Paginated bidder list response."},
    500: {"description": "Database query error."}
})
def list_bidders(page: int = 1, page_size: int = 20, tender_id: str | None = None, db: Session = Depends(get_db)):
    """Route wrapper for BidderService.list_bidders."""
    service = BidderService(db=db)
    try:
        return service.list_bidders(page=page, page_size=page_size, tender_id=tender_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load bidders", "details": {}}},
        ) from exc


@router.get("/bidders/{id}", tags=["Bidders"], summary="Get one bidder", responses={
    200: {"description": "Bidder response."},
    404: {"description": "Bidder not found."},
    500: {"description": "Database query error."}
})
def get_bidder(id: str, db: Session = Depends(get_db)):
    """Route wrapper for BidderService.get_bidder."""
    service = BidderService(db=db)
    try:
        bidder = service.get_bidder(id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load bidder details", "details": {}}},
        ) from exc
    if bidder is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Bidder not found", "details": {}}})
    return bidder


@router.post("/documents/upload", tags=["Documents"], summary="Upload a document", status_code=201, responses={
    201: {"description": "Document metadata response."},
    400: {"description": "Bad request."},
    422: {"description": "Unprocessable entity."}
})
def upload_document(file: UploadFile = File(...), bidder_id: str = Form(...), document_type: str = Form(...), context: dict = Depends(get_api_request_context)):
    """Route wrapper for DocumentService.upload_document."""
    service = DocumentService()
    try:
        return service.upload_document(bidder_id, document_type, file.filename or "demo.pdf", file.content_type or "application/pdf")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": {}}}) from exc


@router.post("/verification/start", tags=["Verification"], summary="Start verification", status_code=201, responses={
    201: {"description": "Verification job response."},
    400: {"description": "Bad request."},
    422: {"description": "Unprocessable entity."}
})
def start_verification(payload: dict = Body(...)):
    """Route wrapper for VerificationService.start_verification."""
    service = VerificationService()
    try:
        return service.start_verification(
            payload.get("bidder_id", ""),
            payload.get("document_id"),
            payload.get("verification_type", "vendor-gst"),
            payload.get("provider", "PAN"),
        )
    except (ValueError, KeyError) as exc:
        detail = str(exc)
        if isinstance(exc, KeyError):
            detail = f"Unknown provider '{payload.get('provider', 'PAN')}'"
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": detail, "details": {}}}) from exc


@router.get("/verification/{id}", tags=["Verification"], summary="Get verification job", responses={
    200: {"description": "Verification job/status response."},
    404: {"description": "Verification record not found."}
})
def get_verification(id: UUID):
    """Route wrapper for VerificationService.get_verification."""
    service = VerificationService()
    verification = service.get_verification(str(id))
    if verification is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Verification job not found", "details": {}}})
    return verification


@router.get("/dashboard/summary", tags=["Dashboard"], summary="Dashboard summary", responses={
    200: {"description": "High-level dashboard placeholder response."}
})
def get_dashboard_summary():
    """Contract placeholder for GET /api/v1/dashboard/summary.

    No live statistics are computed in M10.
    """
    return {
        "total_tenders": 0,
        "total_bidders": 0,
        "pending_verifications": 0,
        "verified_documents": 0,
    }


@router.get("/audit/{id}", tags=["Audit"], summary="Get audit information", responses={
    200: {"description": "Audit placeholder response."},
    404: {"description": "Audit record not found placeholder."}
})
def get_audit(id: UUID):
    """Contract placeholder for GET /api/v1/audit/{id}."""
    return {
        "id": str(id),
        "entity_type": "tender",
        "entity_id": "00000000-0000-0000-0000-000000000000",
        "event": "created",
        "actor": "system",
        "details": {},
        "created_at": "2026-09-11T00:00:00Z",
    }
