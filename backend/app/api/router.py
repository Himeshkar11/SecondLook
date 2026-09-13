"""Versioned FastAPI router for the M09/M10 contract and service boundary.

This router keeps the established API version prefix `/api/v1` and declares
contract-only endpoints for OpenAPI generation. The resource endpoints are
wired to deterministic demo service classes. They do not contain database
queries, CRUD, auth, or verification provider calls.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_api_request_context, get_db
from app.services.bidder_service import BidderService
from app.services.document_service import DocumentService
from app.services.government_verification_service import (
    AIExtractionPrerequisiteError,
    GovernmentVerificationService,
    InvalidIdentifierFormatError,
    MissingIdentifierError,
    UnsupportedDocumentTypeError,
)
from app.services.compliance_service import ComplianceService, NoApprovedRequirementsError
from app.schemas.compliance import (
    BidderComplianceResponse,
    ComplianceEvaluationRead,
    ComplianceEvaluationSummaryItem,
    TenderExtractionRequest,
    TenderExtractionResponse,
    TenderRequirementCreate,
    TenderRequirementRead,
    TenderRequirementUpdate,
)
from app.services.tender_service import TenderService
from app.services.verification_service import VerificationService
from app.workers.jobs import DocumentOCRStatus
from app.workers.worker import DocumentAIWorker, DocumentOCRWorker, DocumentVerificationWorker


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


# ============================================================================
# COMPLIANCE EVALUATION ORCHESTRATION (Task 13)
# Placed before greedy /tenders/{id:path} to prevent route swallowing
# ============================================================================


@router.post(
    "/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluate",
    response_model=ComplianceEvaluationRead,
    tags=["Compliance"],
    summary="Run complete statutory compliance evaluation for a bidder on a tender (Task 13)",
)
def run_compliance_evaluation_endpoint(
    tender_id: str,
    bidder_id: str,
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
):
    """Execute complete deterministic statutory compliance evaluation for a bidder.

    Strictly evaluates ONLY approved tender requirements against resolved multi-source evidence.
    Generates a unique evaluation_id and preserves immutable evaluation history.
    """
    officer_id = payload.get("officer_id") if isinstance(payload, dict) else None
    service = ComplianceService(db=db)
    try:
        return service.run_compliance_evaluation(
            tender_id=tender_id, bidder_id=bidder_id, officer_id=officer_id, allow_empty=False
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": str(exc), "details": {}}},
        ) from exc
    except NoApprovedRequirementsError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "NO_APPROVED_REQUIREMENTS", "message": str(exc), "details": {}}},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": {}}},
        ) from exc
    except Exception as exc:
        logger.error("Failed to run compliance evaluation: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EVALUATION_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.get(
    "/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluations",
    response_model=list[ComplianceEvaluationSummaryItem],
    tags=["Compliance"],
    summary="List all historical compliance evaluation runs for a bidder on a tender (Task 13)",
)
def list_compliance_evaluations_history_endpoint(
    tender_id: str,
    bidder_id: str,
    db: Session = Depends(get_db),
):
    """Fetch immutable audit history of all compliance evaluations executed for this bidder and tender."""
    service = ComplianceService(db=db)
    try:
        return service.get_compliance_evaluations_history(tender_id=tender_id, bidder_id=bidder_id)
    except Exception as exc:
        logger.error("Failed to list compliance evaluation history: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "HISTORY_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.get(
    "/compliance/evaluations/{evaluation_id}",
    response_model=ComplianceEvaluationRead,
    tags=["Compliance"],
    summary="Retrieve a compliance evaluation report by evaluation ID (Task 13)",
)
def get_compliance_evaluation_endpoint(
    evaluation_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full details, summary, and traceable evidence for a specific compliance evaluation run."""
    service = ComplianceService(db=db)
    try:
        eval_read = service.get_compliance_evaluation(evaluation_id=evaluation_id)
        if not eval_read:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": f"Compliance evaluation {evaluation_id} not found", "details": {}}},
            )
        return eval_read
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to retrieve compliance evaluation %s: %s", evaluation_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RETRIEVAL_ERROR", "message": str(exc), "details": {}}},
        ) from exc


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


@router.post("/bidders/{bidder_id}/documents", tags=["Documents"], summary="Upload document for bidder", status_code=201, responses={
    201: {"description": "Document metadata response."},
    400: {"description": "Bad request."},
    404: {"description": "Bidder not found."},
    422: {"description": "Validation error."},
    500: {"description": "Storage or database error."}
})
async def upload_bidder_document(
    bidder_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a document for a specific bidder and trigger asynchronous OCR."""
    service = DocumentService(db=db)
    try:
        content = await file.read()
        res = service.upload_document(
            bidder_id=bidder_id,
            file_bytes=content,
            file_name=file.filename or "document.pdf",
            mime_type=file.content_type or "application/pdf",
            document_type=document_type,
        )

        # Dispatch background OCR job asynchronously without blocking HTTP response
        doc_id = res["id"]

        def _run_ocr_async(d_id: str, f_bytes: bytes):
            worker = DocumentOCRWorker()
            job = worker.process_document_by_id(d_id, content_override=f_bytes)
            if job and job.status == DocumentOCRStatus.OCR_COMPLETED:
                ai_worker = DocumentAIWorker()
                ai_worker.process_document_by_id(d_id)

        background_tasks.add_task(_run_ocr_async, doc_id, content)

        return res
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(exc), "details": {}}}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": {}}}) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "UPLOAD_FAILED", "message": "Failed to upload document", "details": {}}}) from exc


@router.get("/bidders/{bidder_id}/documents", tags=["Documents"], summary="List bidder documents", responses={
    200: {"description": "List of bidder documents."},
    500: {"description": "Database query error."}
})
def list_bidder_documents(bidder_id: str, page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    """List all documents belonging to a bidder."""
    service = DocumentService(db=db)
    try:
        return service.list_documents(bidder_id=bidder_id, page=page, page_size=page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to list bidder documents", "details": {}}}) from exc


@router.post(
    "/tenders/{tender_id}/documents",
    tags=["Tenders", "Documents"],
    summary="Upload a tender document",
)
async def upload_tender_document(
    tender_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form("TENDER_DOCUMENT"),
    db: Session = Depends(get_db),
):
    """Upload a document for a tender and trigger OCR in the background."""
    service = DocumentService(db=db)
    try:
        content = await file.read()
        res = service.upload_document(
            tender_id=tender_id,
            file_bytes=content,
            file_name=file.filename or "tender_document.pdf",
            mime_type=file.content_type or "application/pdf",
            document_type=document_type,
        )

        doc_id = res["id"]

        def _run_ocr_async(d_id: str, f_bytes: bytes):
            worker = DocumentOCRWorker()
            worker.process_document_by_id(d_id, content_override=f_bytes)

        background_tasks.add_task(_run_ocr_async, doc_id, content)

        return res
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(exc), "details": {}}}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": {}}}) from exc
    except Exception as exc:
        logger.error("Failed to upload tender document: %s", exc)
        raise HTTPException(status_code=500, detail={"error": {"code": "UPLOAD_FAILED", "message": "Failed to upload tender document", "details": {}}}) from exc


@router.get(
    "/tenders/{tender_id}/documents",
    tags=["Tenders", "Documents"],
    summary="List tender documents",
)
def list_tender_documents(
    tender_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """List all documents associated with a tender."""
    service = DocumentService(db=db)
    try:
        return service.list_documents(tender_id=tender_id, page=page, page_size=page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to list tender documents", "details": {}}}) from exc


@router.get("/documents", tags=["Documents"], summary="List all documents", responses={
    200: {"description": "List of all documents."},
    500: {"description": "Database query error."}
})
def list_all_documents(
    bidder_id: str | None = None,
    tender_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """List documents across all entities or filter by bidder_id / tender_id."""
    service = DocumentService(db=db)
    try:
        return service.list_documents(bidder_id=bidder_id, tender_id=tender_id, page=page, page_size=page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to list documents", "details": {}}}) from exc


@router.get("/documents/{document_id}/access", tags=["Documents"], summary="Get secure temporary document access URL", responses={
    200: {"description": "Secure temporary download URL."},
    404: {"description": "Document not found."},
    500: {"description": "Storage access error."}
})
def get_document_access(document_id: str, expires_in: int = 3600, db: Session = Depends(get_db)):
    """Generate a short-lived signed access URL for a private stored document."""
    service = DocumentService(db=db)
    try:
        access = service.get_document_access(document_id, expires_in=expires_in)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "STORAGE_ERROR", "message": "Failed to generate document access URL", "details": {}}}) from exc
    if access is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})
    return access


@router.get("/documents/{document_id}/ocr", tags=["Documents"], summary="Get document OCR details", responses={
    200: {"description": "Document OCR status and raw extracted text."},
    404: {"description": "Document not found."},
    500: {"description": "Database query error."}
})
def get_document_ocr(document_id: str, db: Session = Depends(get_db)):
    """Retrieve OCR status and extracted raw text for a document."""
    service = DocumentService(db=db)
    try:
        ocr_info = service.get_document_ocr(document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load document OCR details", "details": {}}}) from exc
    if ocr_info is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})
    return ocr_info


@router.post("/documents/{document_id}/ocr/retry", tags=["Documents"], summary="Retry document OCR processing", responses={
    200: {"description": "Document re-queued for OCR."},
    404: {"description": "Document not found."},
    500: {"description": "Database or worker error."}
})
def retry_document_ocr(document_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Re-queue an OCR job for a failed or stuck document."""
    service = DocumentService(db=db)
    try:
        res = service.retry_document_ocr(document_id)
        if res is None:
            raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})

        def _run_retry():
            worker = DocumentOCRWorker()
            worker.process_document_by_id(document_id)

        background_tasks.add_task(_run_retry)
        return res
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "RETRY_FAILED", "message": str(exc), "details": {}}}) from exc


@router.get("/documents/{document_id}/ai", tags=["Documents"], summary="Get document AI extraction details", responses={
    200: {"description": "Document AI extraction status and structured JSON."},
    404: {"description": "Document not found."},
    500: {"description": "Database query error."}
})
def get_document_ai(document_id: str, db: Session = Depends(get_db)):
    """Retrieve AI extraction status and structured JSON for a document."""
    service = DocumentService(db=db)
    try:
        ai_info = service.get_document_ai(document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load document AI extraction details", "details": {}}}) from exc
    if ai_info is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})
    return ai_info


@router.post("/documents/{document_id}/ai/retry", tags=["Documents"], summary="Retry document AI extraction", responses={
    200: {"description": "Document re-queued for AI extraction."},
    404: {"description": "Document not found."},
    500: {"description": "Database or worker error."}
})
def retry_document_ai(document_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Re-queue an AI extraction job for a failed or stuck document."""
    service = DocumentService(db=db)
    try:
        res = service.retry_document_ai(document_id)
        if res is None:
            raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})

        def _run_ai_retry():
            worker = DocumentAIWorker()
            worker.process_document_by_id(document_id, force_retry=True)

        background_tasks.add_task(_run_ai_retry)
        return res
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "RETRY_FAILED", "message": str(exc), "details": {}}}) from exc


@router.post("/documents/{document_id}/verify", tags=["Documents"], summary="Run statutory government verification", responses={
    200: {"description": "Document verification result."},
    400: {"description": "Prerequisite not met."},
    404: {"description": "Document not found."},
    422: {"description": "Validation or format error."},
    500: {"description": "Internal server error."}
})
def verify_document(document_id: str, db: Session = Depends(get_db)):
    """Trigger statutory government verification for a document with completed AI extraction."""
    service = GovernmentVerificationService(db=db)
    try:
        result = service.verify_document(document_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(exc), "details": {}}}) from exc
    except AIExtractionPrerequisiteError as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "AI_PREREQUISITE_FAILED", "message": str(exc), "details": {}}}) from exc
    except (UnsupportedDocumentTypeError, MissingIdentifierError, InvalidIdentifierFormatError) as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": {}}}) from exc
    except Exception as exc:
        logger.error("Failed to verify document %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail={"error": {"code": "VERIFICATION_FAILED", "message": str(exc), "details": {}}}) from exc


@router.get("/documents/{document_id}/verification", tags=["Documents"], summary="Get document statutory verification details", responses={
    200: {"description": "Document verification details and comparison history."},
    404: {"description": "Document not found."},
    500: {"description": "Database query error."}
})
def get_document_verification(document_id: str, db: Session = Depends(get_db)):
    """Retrieve statutory verification status, field comparisons, and history for a document."""
    service = GovernmentVerificationService(db=db)
    try:
        verification_info = service.get_document_verification(document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load document verification details", "details": {}}}) from exc
    if verification_info is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})
    return verification_info


@router.get("/documents/{document_id}", tags=["Documents"], summary="Get document metadata", responses={

    200: {"description": "Document metadata."},
    404: {"description": "Document not found."},
    500: {"description": "Database query error."}
})
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata for a specific document."""
    service = DocumentService(db=db)
    try:
        doc = service.get_document(document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load document", "details": {}}}) from exc
    if doc is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})
    return doc



@router.post("/documents/upload", tags=["Documents"], summary="Upload a document", status_code=201, responses={
    201: {"description": "Document metadata response."},
    400: {"description": "Bad request."},
    422: {"description": "Unprocessable entity."}
})
def upload_document(
    file: UploadFile = File(...),
    bidder_id: str = Form(...),
    document_type: str = Form(...),
    context: dict = Depends(get_api_request_context),
):
    """Route wrapper for DocumentService.upload_document (legacy contract endpoint)."""
    service = DocumentService()
    try:
        return service.upload_document(
            bidder_id=bidder_id,
            document_type=document_type,
            file_name=file.filename or "demo.pdf",
            mime_type=file.content_type or "application/pdf",
        )
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


# ============================================================================
# COMPLIANCE ENGINE & TENDER REQUIREMENTS (Task 11)
# Layer 3: Factual statutory requirement evaluation. No procurement decisions.
# ============================================================================


def _to_requirement_read(r) -> TenderRequirementRead:
    return TenderRequirementRead(
        id=r.id,
        tender_id=r.tender_id,
        code=r.code,
        title=r.title,
        description=r.description,
        type=r.type,
        mandatory=r.mandatory,
        display_order=r.display_order,
        status=getattr(r, "status", "APPROVED"),
        rule_type=getattr(r, "rule_type", None),
        parameters=getattr(r, "parameters", None),
        rule_config=r.rule_config if isinstance(r.rule_config, list) else [r.rule_config] if r.rule_config else [],
        source_document_id=getattr(r, "source_document_id", None),
        source_text=getattr(r, "source_text", None),
        source_page=getattr(r, "source_page", None),
        source_section=getattr(r, "source_section", None),
        created_by=getattr(r, "created_by", None),
        approved_by=getattr(r, "approved_by", None),
        created_at=r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else r.created_at,
        updated_at=r.updated_at.isoformat() if hasattr(r.updated_at, "isoformat") else r.updated_at,
        approved_at=r.approved_at.isoformat() if hasattr(r.approved_at, "isoformat") else r.approved_at,
    )


@router.get(
    "/tenders/{tender_id}/requirements",
    response_model=list[TenderRequirementRead],
    tags=["Compliance"],
    summary="Get statutory requirements for a tender",
)
def get_tender_requirements(
    tender_id: str,
    status: Optional[str] = Query(None, description="Filter by requirement status"),
    db: Session = Depends(get_db),
):
    """Fetch statutory requirements defined for a tender, optionally filtered by status."""
    service = ComplianceService(db=db)
    try:
        reqs = service.get_tender_requirements(tender_id, status=status)
        return [_to_requirement_read(r) for r in reqs]
    except Exception as exc:
        logger.error("Failed to load tender requirements: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.post(
    "/tenders/{tender_id}/requirements",
    response_model=TenderRequirementRead,
    tags=["Compliance"],
    summary="Create a statutory requirement for a tender",
)
def create_tender_requirement(
    tender_id: str,
    payload: TenderRequirementCreate,
    db: Session = Depends(get_db),
):
    """Add a new requirement to a tender. Initial status is UNDER_REVIEW or DRAFT."""
    service = ComplianceService(db=db)
    try:
        r = service.create_tender_requirement(tender_id, payload)
        return _to_requirement_read(r)
    except Exception as exc:
        logger.error("Failed to create tender requirement: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "CREATION_FAILED", "message": str(exc), "details": {}}},
        ) from exc


@router.post(
    "/tenders/{tender_id}/requirements/extract",
    response_model=TenderExtractionResponse,
    tags=["Compliance"],
    summary="Extract requirements from tender text or document using AI",
)
def extract_tender_requirements(
    tender_id: str,
    payload: TenderExtractionRequest = Body(...),
    db: Session = Depends(get_db),
):
    """Extract candidate requirements from tender document or text.
    
    All candidates are saved with status AI_SUGGESTED and must be reviewed and approved
    by a procurement officer before entering the Compliance Engine.
    """
    service = ComplianceService(db=db)
    try:
        reqs = service.extract_tender_requirements(
            tender_id=tender_id,
            text=payload.text,
            document_id=payload.document_id,
        )
        return TenderExtractionResponse(
            tender_id=tender_id,
            extracted_count=len(reqs),
            requirements=[_to_requirement_read(r) for r in reqs],
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": str(exc), "details": {}}},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "EXTRACTION_FAILED", "message": str(exc), "details": {}}},
        ) from exc
    except Exception as exc:
        logger.error("Failed to extract tender requirements: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EXTRACTION_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.get(
    "/tender-requirements/{requirement_id}",
    response_model=TenderRequirementRead,
    tags=["Compliance"],
    summary="Get single tender requirement by ID",
)
def get_single_tender_requirement(
    requirement_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve a single requirement by ID."""
    service = ComplianceService(db=db)
    req = service.get_tender_requirement(requirement_id)
    if req is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Requirement {requirement_id} not found", "details": {}}},
        )
    return _to_requirement_read(req)


@router.patch(
    "/tender-requirements/{requirement_id}",
    response_model=TenderRequirementRead,
    tags=["Compliance"],
    summary="Update a tender requirement",
)
def update_tender_requirement(
    requirement_id: str,
    payload: TenderRequirementUpdate = Body(...),
    db: Session = Depends(get_db),
):
    """Update requirement parameters.
    
    Direct escalation to APPROVED is rejected.
    Modifying an APPROVED requirement demotes it to UNDER_REVIEW.
    """
    service = ComplianceService(db=db)
    try:
        r = service.update_tender_requirement(requirement_id, payload)
        return _to_requirement_read(r)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": str(exc), "details": {}}},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_TRANSITION", "message": str(exc), "details": {}}},
        ) from exc
    except Exception as exc:
        logger.error("Failed to update tender requirement: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "UPDATE_FAILED", "message": str(exc), "details": {}}},
        ) from exc


@router.post(
    "/tender-requirements/{requirement_id}/approve",
    response_model=TenderRequirementRead,
    tags=["Compliance"],
    summary="Approve a tender requirement",
)
def approve_tender_requirement(
    requirement_id: str,
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
):
    """Explicitly approve a requirement by a procurement officer."""
    officer_id = payload.get("officer_id") if isinstance(payload, dict) else None
    service = ComplianceService(db=db)
    try:
        r = service.approve_requirement(requirement_id, officer_id=officer_id)
        return _to_requirement_read(r)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": str(exc), "details": {}}},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "APPROVAL_ERROR", "message": str(exc), "details": {}}},
        ) from exc
    except Exception as exc:
        logger.error("Failed to approve tender requirement: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "APPROVAL_FAILED", "message": str(exc), "details": {}}},
        ) from exc


@router.post(
    "/tender-requirements/{requirement_id}/reject",
    response_model=TenderRequirementRead,
    tags=["Compliance"],
    summary="Reject a tender requirement",
)
def reject_tender_requirement(
    requirement_id: str,
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
):
    """Reject a requirement candidate."""
    reason = payload.get("reason") if isinstance(payload, dict) else None
    service = ComplianceService(db=db)
    try:
        r = service.reject_requirement(requirement_id, reason=reason)
        return _to_requirement_read(r)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": str(exc), "details": {}}},
        ) from exc
    except Exception as exc:
        logger.error("Failed to reject tender requirement: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "REJECTION_FAILED", "message": str(exc), "details": {}}},
        ) from exc


@router.get(
    "/bidders/{bidder_id}/compliance",
    response_model=BidderComplianceResponse,
    tags=["Compliance"],
    summary="Get bidder statutory compliance evaluation for a tender",
)
def get_bidder_compliance(
    bidder_id: str,
    tender_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve or run factual compliance evaluations of tender requirements against verified evidence."""
    service = ComplianceService(db=db)
    try:
        return service.get_bidder_compliance(tender_id=tender_id, bidder_id=bidder_id)
    except Exception as exc:
        logger.error("Failed to get bidder compliance: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EVALUATION_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.post(
    "/bidders/{bidder_id}/compliance/evaluate",
    response_model=BidderComplianceResponse,
    tags=["Compliance"],
    summary="Trigger compliance evaluation for a bidder against tender requirements",
)
def evaluate_bidder_compliance(
    bidder_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Execute fresh deterministic compliance evaluation against verified evidence."""
    tender_id = payload.get("tender_id")
    if not tender_id:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "tender_id is required in body", "details": {}}},
        )
    service = ComplianceService(db=db)
    try:
        return service.evaluate_bidder_compliance(tender_id=tender_id, bidder_id=bidder_id)
    except Exception as exc:
        logger.error("Failed to evaluate bidder compliance: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EVALUATION_ERROR", "message": str(exc), "details": {}}},
        ) from exc
