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

from app.auth.dependencies import get_authenticated_identity, get_supabase_auth_user
from app.auth.service import SupabaseAuthUser
from app.authz.dependencies import (
    require_document_access,
    require_authenticated_user,
    require_bidder,
    require_bidder_or_officer_bidder,
    require_evaluation_access,
    require_officer,
    require_owned_bidder,
    require_owned_bidder_by_id,
    require_tender_bidder_access,
)
from app.api.deps import get_api_request_context, get_db
from app.models.user import User
from app.schemas.bidder import BidderProfileResponse
from app.schemas.bid import BidCreateRequest, BidDocumentRead, BidRead, BidSubmitResponse
from app.schemas.bidder_compliance import BidderComplianceHistoryItem, BidderComplianceViewResponse
from app.services.bid_service import BidService
from app.services.bidder_service import BidderService
from app.services.document_service import DocumentService

from app.services.government_verification_service import (
    AIExtractionPrerequisiteError,
    GovernmentVerificationService,
    InvalidIdentifierFormatError,
    MissingIdentifierError,
    UnsupportedDocumentTypeError,
)
from app.schemas.audit_log import AuditLogListResponse, AuditLogRead
from app.schemas.compliance import (
    BidderComplianceResponse,
    ComplianceEvaluationRead,
    ComplianceEvaluationSummaryItem,
    EvaluationEvidenceTraceResponse,
    EvidenceTraceChainRead,
    NormalizedEvidenceItemRead,
    TenderExtractionRequest,
    TenderExtractionResponse,
    TenderRequirementCreate,
    TenderRequirementRead,
    TenderRequirementUpdate,
)
from app.services.audit_service import AuditService, get_audit_service
from app.services.compliance_service import ComplianceService, NoApprovedRequirementsError
from app.services.tender_service import TenderService
from app.services.verification_service import VerificationService
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.tender_requirement import TenderRequirement
from app.schemas.auth import (
    AuthenticatedApplicationUserRead,
    SignupProvisionRequest,
    SignupProvisionResponse,
)
from app.services.signup_service import SignupProvisioningService
from app.workers.jobs import DocumentOCRStatus
from app.workers.worker import DocumentAIWorker, DocumentOCRWorker, DocumentVerificationWorker


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.get("/auth/me", response_model=AuthenticatedApplicationUserRead, tags=["Authentication"], summary="Get authenticated application identity")
def get_authenticated_application_user(identity=Depends(get_authenticated_identity)):
    """Resolve the bearer token to its linked application user.

    This endpoint establishes identity only; it does not authorize any role or
    protect the existing domain routes.
    """
    user = identity.application_user
    return AuthenticatedApplicationUserRead(
        user_id=user.id,
        auth_user_id=identity.auth_user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.post(
    "/auth/provision",
    response_model=SignupProvisionResponse,
    status_code=201,
    tags=["Authentication"],
    summary="Create the application profile for a Supabase Auth account",
)
def provision_application_user(
    payload: SignupProvisionRequest,
    auth_user: SupabaseAuthUser = Depends(get_supabase_auth_user),
    db: Session = Depends(get_db),
):
    """Create exactly one role-specific application profile after Auth signup.

    This endpoint creates identity/profile records only. It does not grant
    access to existing business APIs or enforce role authorization.
    """
    if db is None:
        return JSONResponse(
            status_code=503,
            content={"detail": "Application identity service is unavailable."},
        )
    return SignupProvisioningService().provision(db, auth_user, payload)


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
def list_tenders(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
):
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
def get_tender_bidders(
    id: str,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
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
    _officer=Depends(require_officer),
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
    _bidder=Depends(require_tender_bidder_access),
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
    _evaluation=Depends(require_evaluation_access),
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


@router.get(
    "/compliance/evaluations/{evaluation_id}/evidence",
    response_model=EvaluationEvidenceTraceResponse,
    tags=["Compliance"],
    summary="Get full evidence trace chains for a compliance evaluation (Task 15)",
)
def get_compliance_evaluation_evidence_endpoint(
    evaluation_id: str,
    db: Session = Depends(get_db),
    _evaluation=Depends(require_evaluation_access),
):
    """Retrieve complete evidence trace chains connecting requirements to original secure files."""
    service = ComplianceService(db=db)
    try:
        return service.get_evaluation_evidence_traces(evaluation_id=evaluation_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": str(exc), "details": {}}},
        ) from exc
    except Exception as exc:
        logger.error("Failed to retrieve evidence trace for evaluation %s: %s", evaluation_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RETRIEVAL_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.get(
    "/compliance/evaluations/{evaluation_id}/audit",
    response_model=list[AuditLogRead],
    tags=["Compliance", "Audit"],
    summary="Get audit events for a compliance evaluation (Task 15)",
)
def get_compliance_evaluation_audit_endpoint(
    evaluation_id: str,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    """Retrieve audit events associated with a compliance evaluation run."""
    service = AuditService(db=db)
    try:
        items, _ = service.list_events(entity_id=evaluation_id, limit=100)
        return items
    except Exception as exc:
        logger.error("Failed to retrieve audit events for evaluation %s: %s", evaluation_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RETRIEVAL_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.get(
    "/requirements/{requirement_id}/evidence",
    response_model=EvidenceTraceChainRead,
    tags=["Compliance"],
    summary="Get evidence trace chain for a specific requirement (Task 15)",
)
@router.get(
    "/tender-requirements/{requirement_id}/evidence",
    response_model=EvidenceTraceChainRead,
    tags=["Compliance"],
    summary="Get evidence trace chain for a specific tender requirement (Task 15)",
)
def get_requirement_evidence_endpoint(
    requirement_id: str,
    bidder_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    """Retrieve evidence trace chain for an individual tender requirement."""
    service = ComplianceService(db=db)
    try:
        trace = service.get_requirement_evidence_trace(requirement_id=requirement_id, bidder_id=bidder_id)
        if not trace:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": f"Requirement {requirement_id} not found", "details": {}}},
            )
        return trace
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to retrieve requirement evidence trace %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RETRIEVAL_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.get(
    "/evidence/{evidence_id}",
    response_model=dict,
    tags=["Compliance"],
    summary="Get individual evidence item details (Task 15)",
)
def get_evidence_item_endpoint(
    evidence_id: str,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    """Retrieve details and trace for a specific evidence item."""
    try:
        e_uuid = UUID(str(evidence_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_ID", "message": "Invalid evidence ID format", "details": {}}},
        )

    from app.models.government_verification import GovernmentVerification
    from app.models.document import Document

    gv = db.get(GovernmentVerification, e_uuid)
    if gv:
        return {
            "evidence_id": str(gv.id),
            "source_type": "GOVERNMENT_VERIFICATION",
            "source": gv.source,
            "document_id": str(gv.document_id) if gv.document_id else None,
            "verification_id": str(gv.id),
            "identifier": gv.identifier,
            "status": gv.status,
            "result": gv.verification_result,
            "verified": gv.status == "COMPLETED" and gv.verification_result in ["MATCH", "VERIFIED", "CLEAR", "LISTED"],
            "government_data": gv.government_data or {},
            "field_results": gv.field_results or {},
            "retrieved_at": gv.retrieved_at.isoformat() if gv.retrieved_at else None,
        }

    doc = db.get(Document, e_uuid)
    if doc:
        return {
            "evidence_id": str(doc.id),
            "source_type": "DOCUMENT",
            "source": doc.document_type or "DOCUMENT",
            "document_id": str(doc.id),
            "file_name": doc.file_name,
            "mime_type": doc.mime_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "ocr_status": doc.ocr_status,
            "ai_status": doc.ai_status,
            "ai_extraction": doc.ai_extraction,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        }

    raise HTTPException(
        status_code=404,
        detail={"error": {"code": "NOT_FOUND", "message": f"Evidence {evidence_id} not found", "details": {}}},
    )


@router.get(
    "/audit/events",
    response_model=AuditLogListResponse,
    tags=["Audit"],
    summary="List system audit events with filtering (Task 15)",
)
def list_audit_events_endpoint(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    """Query immutable audit events for security, verification, and compliance monitoring."""
    service = AuditService(db=db)
    try:
        items, total = service.list_events(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        return AuditLogListResponse(
            items=[AuditLogRead.model_validate(i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        logger.error("Failed to list audit events: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RETRIEVAL_ERROR", "message": str(exc), "details": {}}},
        ) from exc


@router.get("/bidders", tags=["Bidders"], summary="List bidders", responses={
    200: {"description": "Paginated bidder list response."},
    500: {"description": "Database query error."}
})
def list_bidders(
    page: int = 1,
    page_size: int = 20,
    tender_id: str | None = None,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    """Route wrapper for BidderService.list_bidders."""
    service = BidderService(db=db)
    try:
        return service.list_bidders(page=page, page_size=page_size, tender_id=tender_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load bidders", "details": {}}},
        ) from exc


@router.get(
    "/bidders/me",
    response_model=BidderProfileResponse,
    tags=["Bidders"],
    summary="Get current authenticated bidder profile and workspace metrics",
    responses={
        200: {"description": "Current bidder profile and workspace counts."},
        401: {"description": "Authentication required."},
        403: {"description": "Forbidden for non-bidder roles."},
        404: {"description": "Bidder profile not found."},
        500: {"description": "Database query error."},
    },
)
def get_current_bidder_profile(
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """Retrieve the profile and workspace statistics for the authenticated bidder.

    Identity and ownership are derived strictly from the authenticated application user,
    preventing any cross-bidder data leakage.
    """
    service = BidderService(db=db)
    try:
        profile = service.get_bidder_profile_by_user_id(current_user.id)
    except Exception as exc:
        logger.error("Failed to retrieve current bidder profile: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Unable to load bidder profile", "details": {}}},
        ) from exc
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Bidder profile not found", "details": {}}},
        )
    return BidderProfileResponse.model_validate(profile)


# ---------------------------------------------------------------------------
# Milestone 08: Authenticated Bidder Bid Submission & Document Workspace
# ---------------------------------------------------------------------------

@router.post(
    "/bidder/tenders/{tender_id}/bids",
    response_model=BidRead,
    tags=["Bidder Bids"],
    summary="Start or retrieve a tender bid submission workspace",
    status_code=201,
)
def create_or_get_tender_bid(
    tender_id: str,
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """Start or open a draft bid workspace for a tender. Idempotent."""
    try:
        t_uuid = UUID(tender_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid tender ID format."}})
    service = BidService(db=db)
    return service.get_or_create_bid(current_user.id, t_uuid)


@router.get(
    "/bidder/bids",
    response_model=list[BidRead],
    tags=["Bidder Bids"],
    summary="List all bids belonging to the authenticated bidder",
)
def list_my_bids(
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """List all bids created by the authenticated bidder."""
    service = BidService(db=db)
    return service.list_bids_for_user(current_user.id)


@router.get(
    "/bidder/bids/{bid_id}",
    response_model=BidRead,
    tags=["Bidder Bids"],
    summary="Get bid workspace details and document statuses",
)
def get_my_bid(
    bid_id: str,
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific bid owned by the authenticated bidder."""
    try:
        b_uuid = UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid bid ID format."}})
    service = BidService(db=db)
    return service.get_bid_for_user(current_user.id, b_uuid)


@router.post(
    "/bidder/bids/{bid_id}/documents",
    tags=["Bidder Bids", "Documents"],
    summary="Upload document to a draft bid workspace",
    status_code=201,
)
async def upload_bid_document(
    bid_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """Upload a document to a draft bid workspace and dispatch OCR/AI workers."""
    try:
        b_uuid = UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid bid ID format."}})
    service = BidService(db=db)
    return await service.upload_bid_document(
        current_user_id=current_user.id,
        bid_id=b_uuid,
        file=file,
        document_type=document_type,
        background_tasks=background_tasks,
    )


@router.post(
    "/bidder/bids/{bid_id}/submit",
    response_model=BidSubmitResponse,
    tags=["Bidder Bids"],
    summary="Formally submit a bid for evaluation",
)
def submit_bid(
    bid_id: str,
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """Formally submit a bid proposal.

    Submission locks the bid and registers it for evaluation.
    It does NOT qualify, approve, reject, or award the bid.
    """
    try:
        b_uuid = UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid bid ID format."}})
    service = BidService(db=db)
    return service.submit_bid(current_user.id, b_uuid)


# ---------------------------------------------------------------------------
# Milestone 09: Authenticated Bidder Compliance Score & Failure Explanation
# ---------------------------------------------------------------------------

@router.get(
    "/bidder/bids/{bid_id}/compliance",
    response_model=BidderComplianceViewResponse,
    tags=["Bidder Compliance"],
    summary="Get factual compliance assessment, deterministic score, and explanations for own bid",
)
def get_bid_compliance_endpoint(
    bid_id: str,
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """Retrieve compliance evaluation, score, requirement statuses, and explanations for a bid.

    Ownership is strictly enforced: Bidders may only view compliance assessments
    for their own bids. The score and explanations are strictly informational.
    """
    try:
        b_uuid = UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid bid ID format."}})
    service = BidService(db=db)
    return service.get_bid_compliance(current_user.id, b_uuid)


@router.get(
    "/bidder/bids/{bid_id}/compliance/history",
    response_model=list[BidderComplianceHistoryItem],
    tags=["Bidder Compliance"],
    summary="Get historical compliance evaluation runs for own bid",
)
def get_bid_compliance_history_endpoint(
    bid_id: str,
    current_user: User = Depends(require_bidder),
    db: Session = Depends(get_db),
):
    """Retrieve immutable audit history of all compliance evaluation runs for this bid."""
    try:
        b_uuid = UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid bid ID format."}})
    service = BidService(db=db)
    return service.get_bid_compliance_history(current_user.id, b_uuid)



@router.get("/bidders/{id}", tags=["Bidders"], summary="Get own bidder profile", responses={

    200: {"description": "Bidder response."},
    404: {"description": "Bidder not found."},
    500: {"description": "Database query error."}
})
def get_bidder(
    id: str,
    db: Session = Depends(get_db),
    _owned_bidder: Bidder = Depends(require_owned_bidder_by_id),
):
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
    _owned_bidder: Bidder = Depends(require_owned_bidder),
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
def list_bidder_documents(
    bidder_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _owned_bidder: Bidder = Depends(require_owned_bidder),
):
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
    _officer=Depends(require_officer),
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
            job = worker.process_document_by_id(d_id, content_override=f_bytes)
            if job and job.status == DocumentOCRStatus.OCR_COMPLETED:
                ai_job = DocumentAIWorker().process_document_by_id(d_id)
                if ai_job and getattr(ai_job, "status", None) == "AI_COMPLETED":
                    doc = DocumentService().get_document(d_id)
                    if doc and doc.get("tender_id"):
                        ComplianceService().extract_tender_requirements(
                            tender_id=doc["tender_id"], document_id=d_id
                        )

        background_tasks.add_task(_run_ocr_async, doc_id, content)

        return res
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(exc), "details": {}}}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": {}}}) from exc
    except Exception as exc:
        logger.error("Failed to upload tender document: %s", exc)
        raise HTTPException(status_code=500, detail={"error": {"code": "UPLOAD_FAILED", "message": "Failed to upload tender document", "details": {}}}) from exc


@router.post(
    "/tenders/{tender_id}/documents/{document_id}/process",
    tags=["Tenders", "Documents"],
    summary="Process a tender document through existing OCR and AI workers",
)
def process_tender_document(
    tender_id: str,
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    try:
        document_uuid = UUID(document_id)
    except (ValueError, TypeError):
        document_uuid = None
    doc = db.get(Document, document_uuid) if document_uuid else None
    if doc is None or str(doc.tender_id) != tender_id:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Tender document not found", "details": {}}})

    def _process():
        ocr_job = DocumentOCRWorker().process_document_by_id(document_id)
        if ocr_job and ocr_job.status == DocumentOCRStatus.OCR_COMPLETED:
            ai_job = DocumentAIWorker().process_document_by_id(document_id)
            if ai_job and getattr(ai_job, "status", None) == "AI_COMPLETED":
                ComplianceService().extract_tender_requirements(tender_id=tender_id, document_id=document_id)

    background_tasks.add_task(_process)
    return {"document_id": document_id, "status": "QUEUED"}


@router.get(
    "/tenders/{tender_id}/documents/{document_id}/processing",
    tags=["Tenders", "Documents"],
    summary="Get tender document OCR and AI processing status",
)
def get_tender_document_processing(
    tender_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    try:
        document_uuid = UUID(document_id)
    except (ValueError, TypeError):
        document_uuid = None
    doc = db.get(Document, document_uuid) if document_uuid else None
    if doc is None or str(doc.tender_id) != tender_id:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Tender document not found", "details": {}}})
    count = db.query(TenderRequirement).filter(TenderRequirement.source_document_id == doc.id).count()
    return {
        "document_id": document_id,
        "ocr_status": doc.ocr_status,
        "ai_status": doc.ai_status,
        "requirements_found": count,
        "last_updated": doc.updated_at.isoformat() if doc.updated_at else None,
    }


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
    _officer=Depends(require_officer),
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
    _officer=Depends(require_officer),
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
def get_document_access(
    document_id: str,
    expires_in: int = 3600,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
    """Generate a short-lived signed access URL for a private stored document."""
    service = DocumentService(db=db)
    try:
        access = service.get_document_access(document_id, expires_in=expires_in)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "STORAGE_ERROR", "message": "Failed to generate document access URL", "details": {}}}) from exc
    if access is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Document not found", "details": {}}})

    try:
        AuditService(db=db).record_event(
            action="DOCUMENT_ACCESSED",
            entity_type="DOCUMENT",
            entity_id=document_id,
            details={"document_id": document_id, "expires_in": expires_in},
            session=db,
        )
    except Exception as audit_err:
        logger.warning("Failed to record document access audit event: %s", audit_err)

    return access


@router.get("/documents/{document_id}/ocr", tags=["Documents"], summary="Get document OCR details", responses={
    200: {"description": "Document OCR status and raw extracted text."},
    404: {"description": "Document not found."},
    500: {"description": "Database query error."}
})
def get_document_ocr(
    document_id: str,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
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
def retry_document_ocr(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
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
def get_document_ai(
    document_id: str,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
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
def retry_document_ai(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
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
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "OCR_PREREQUISITE_NOT_MET", "message": str(exc), "details": {}}},
        ) from exc
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
def verify_document(
    document_id: str,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
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
def get_document_verification(
    document_id: str,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
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
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    _document: Document = Depends(require_document_access),
):
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
    _officer=Depends(require_officer),
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
def start_verification(
    payload: dict = Body(...),
    _officer=Depends(require_officer),
):
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
def get_verification(
    id: UUID,
    _officer=Depends(require_officer),
):
    """Route wrapper for VerificationService.get_verification."""
    service = VerificationService()
    verification = service.get_verification(str(id))
    if verification is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Verification job not found", "details": {}}})
    return verification


@router.get("/dashboard/summary", tags=["Dashboard"], summary="Dashboard summary", responses={
    200: {"description": "High-level dashboard placeholder response."}
})
def get_dashboard_summary(
    _officer=Depends(require_officer),
):
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
def get_audit(
    id: UUID,
    _officer=Depends(require_officer),
):
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
        rejection_reason=getattr(r, "rejection_reason", None),
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
    _officer=Depends(require_officer),
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
    _officer=Depends(require_officer),
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
    _officer=Depends(require_officer),
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
    _officer=Depends(require_officer),
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
    _officer=Depends(require_officer),
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
    officer=Depends(require_officer),
):
    """Explicitly approve a requirement by a procurement officer."""
    officer_id = str(officer.id)
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
    _officer=Depends(require_officer),
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
    _bidder=Depends(require_tender_bidder_access),
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
    _officer=Depends(require_officer),
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


@router.get("/tenders/{id:path}", tags=["Tenders"], summary="Get one tender", responses={
    200: {"description": "Tender response."},
    404: {"description": "Tender not found."},
    500: {"description": "Database query error."}
})
def get_tender(
    id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
):
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
