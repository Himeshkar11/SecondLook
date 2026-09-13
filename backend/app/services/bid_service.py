"""Domain service for managing Bid submission workspaces (Milestone 08).

Handles bid creation, listing, detail retrieval with document processing states,
document attachment, and formal bid submission.
All operations derive ownership strictly from authenticated identity.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.bid import Bid
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.tender import Tender, tender_bidders
from app.schemas.bid import BidDocumentRead, BidRead, BidSubmitResponse
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.workers.jobs import DocumentAIStatus, DocumentOCRStatus
from app.workers.worker import DocumentAIWorker, DocumentOCRWorker

logger = logging.getLogger(__name__)


class BidService:
    """Service encapsulating Bid submission operations and security checks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_bidder_for_user(self, user_id: UUID) -> Bidder:
        """Resolve Bidder record for the authenticated application user."""
        bidder = self.db.scalar(select(Bidder).where(Bidder.user_id == user_id))
        if bidder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "BIDDER_NOT_FOUND", "message": "No bidder profile found for current user."}},
            )
        return bidder

    def _map_bid_to_read(self, bid: Bid) -> BidRead:
        """Map Bid ORM model to BidRead schema with tender metadata and document processing state."""
        tender = bid.tender
        docs_read = [
            BidDocumentRead(
                id=doc.id,
                file_name=doc.file_name,
                document_type=doc.document_type,
                file_size=doc.file_size,
                mime_type=doc.mime_type,
                status=doc.status,
                ocr_status=doc.ocr_status,
                ai_status=doc.ai_status,
                verification_status=doc.verification_status,
                uploaded_at=doc.uploaded_at,
                updated_at=doc.updated_at,
            )
            for doc in bid.documents
        ]

        return BidRead(
            id=bid.id,
            bidder_id=bid.bidder_id,
            tender_id=bid.tender_id,
            status=bid.status,
            submitted_at=bid.submitted_at,
            created_at=bid.created_at,
            updated_at=bid.updated_at,
            tender_title=tender.title if tender else None,
            tender_reference_number=tender.reference_number if tender else None,
            tender_organization="Public Sector / Ministry",
            tender_status=tender.status if tender else None,
            tender_closing_date=None,
            documents_count=len(docs_read),
            documents=docs_read,
        )

    def get_or_create_bid(self, current_user_id: UUID, tender_id: UUID) -> BidRead:
        """Start or retrieve existing draft bid workspace for a tender.

        Idempotent: if the bidder already started a bid for this tender, returns the existing one.
        """
        bidder = self._get_bidder_for_user(current_user_id)

        tender = self.db.scalar(select(Tender).where(Tender.id == tender_id))
        if tender is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "TENDER_NOT_FOUND", "message": f"Tender {tender_id} not found."}},
            )

        # Check existing bid
        bid = self.db.scalar(select(Bid).where(Bid.bidder_id == bidder.id, Bid.tender_id == tender_id))
        if bid is not None:
            return self._map_bid_to_read(bid)

        # Create new bid in DRAFT status
        now = datetime.now(timezone.utc)
        bid = Bid(
            id=uuid.uuid4(),
            bidder_id=bidder.id,
            tender_id=tender.id,
            status="DRAFT",
            submitted_at=None,
            created_at=now,
            updated_at=now,
        )
        self.db.add(bid)

        # Ensure tender_bidders association exists
        assoc_exists = self.db.scalar(
            select(tender_bidders.c.tender_id).where(
                tender_bidders.c.tender_id == tender.id,
                tender_bidders.c.bidder_id == bidder.id,
            )
        )
        if not assoc_exists:
            self.db.execute(
                tender_bidders.insert().values(
                    tender_id=tender.id,
                    bidder_id=bidder.id,
                    created_at=now,
                )
            )

        self.db.commit()
        self.db.refresh(bid)

        try:
            AuditService(db=self.db).record_event(
                action="BID_CREATED",
                entity_type="BID",
                entity_id=bid.id,
                user_id=current_user_id,
                details={"bidder_id": str(bidder.id), "tender_id": str(tender_id)},
                session=self.db,
            )
        except Exception as audit_err:
            logger.warning("Failed to record BID_CREATED audit event: %s", audit_err)

        return self._map_bid_to_read(bid)

    def list_bids_for_user(self, current_user_id: UUID) -> List[BidRead]:
        """List all bids belonging to the authenticated bidder."""
        bidder = self._get_bidder_for_user(current_user_id)
        bids = self.db.scalars(
            select(Bid).where(Bid.bidder_id == bidder.id).order_by(desc(Bid.updated_at))
        ).all()
        return [self._map_bid_to_read(b) for b in bids]

    def get_bid_for_user(self, current_user_id: UUID, bid_id: UUID) -> BidRead:
        """Get bid details and attached document states for the authenticated bidder."""
        bidder = self._get_bidder_for_user(current_user_id)
        bid = self.db.scalar(select(Bid).where(Bid.id == bid_id))
        if bid is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "BID_NOT_FOUND", "message": "Bid workspace not found."}},
            )

        if bid.bidder_id != bidder.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "FORBIDDEN", "message": "You do not own this bid."}},
            )

        return self._map_bid_to_read(bid)

    async def upload_bid_document(
        self,
        current_user_id: UUID,
        bid_id: UUID,
        file: UploadFile,
        document_type: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Upload a document to an existing draft bid and trigger OCR/AI background workers."""
        bidder = self._get_bidder_for_user(current_user_id)
        bid = self.db.scalar(select(Bid).where(Bid.id == bid_id))
        if bid is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "BID_NOT_FOUND", "message": "Bid workspace not found."}},
            )

        if bid.bidder_id != bidder.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "FORBIDDEN", "message": "You do not own this bid."}},
            )

        if bid.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "BID_LOCKED", "message": "Cannot upload documents to a submitted bid."}},
            )

        content = await file.read()
        doc_service = DocumentService(db=self.db)
        try:
            res = doc_service.upload_document(
                bidder_id=str(bidder.id),
                tender_id=str(bid.tender_id),
                bid_id=str(bid.id),
                file_bytes=content,
                file_name=file.filename or "bid_document.pdf",
                mime_type=file.content_type or "application/pdf",
                document_type=document_type,
                enqueue_ocr=True,
            )

            # Dispatch background OCR and AI extraction using existing workers
            doc_id = res["id"]

            def _run_ocr_and_ai(d_id: str, f_bytes: bytes):
                worker = DocumentOCRWorker()
                job = worker.process_document_by_id(d_id, content_override=f_bytes)
                if job and job.status == DocumentOCRStatus.OCR_COMPLETED:
                    ai_worker = DocumentAIWorker()
                    ai_job = ai_worker.process_document_by_id(d_id)
                    if ai_job and getattr(ai_job, "status", None) == DocumentAIStatus.AI_COMPLETED:
                        from app.services.government_verification_service import SUPPORTED_DOCUMENT_TYPES
                        doc_item = DocumentService().get_document(d_id)
                        raw_t = ((doc_item.get("document_type") if doc_item else "") or "").upper()
                        if raw_t in ("MSME",):
                            raw_t = "UDYAM"
                        if raw_t in SUPPORTED_DOCUMENT_TYPES:
                            try:
                                from app.workers.worker import DocumentVerificationWorker
                                DocumentVerificationWorker().process_document_by_id(d_id)
                            except Exception as gv_exc:
                                logger.warning("Automatic statutory verification for doc %s skipped or failed: %s", d_id, gv_exc)

            background_tasks.add_task(_run_ocr_and_ai, doc_id, content)

            bid.updated_at = datetime.now(timezone.utc)
            self.db.commit()

            try:
                AuditService(db=self.db).record_event(
                    action="BID_DOCUMENT_UPLOADED",
                    entity_type="BID",
                    entity_id=bid.id,
                    user_id=current_user_id,
                    details={"document_id": doc_id, "document_type": document_type},
                    session=self.db,
                )
            except Exception as audit_err:
                logger.warning("Failed to record BID_DOCUMENT_UPLOADED audit event: %s", audit_err)

            return res
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(exc)}}) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}) from exc
        except Exception as exc:
            logger.error("Failed to upload bid document: %s", exc)
            raise HTTPException(status_code=500, detail={"error": {"code": "UPLOAD_FAILED", "message": "Failed to upload bid document."}}) from exc

    def submit_bid(self, current_user_id: UUID, bid_id: UUID) -> BidSubmitResponse:
        """Submit a bid for formal evaluation.

        SUBMISSION RULES:
        1. Only the owner can submit.
        2. Bid must currently be in DRAFT status.
        3. At least one document must be attached.
        4. Submission sets status='SUBMITTED' and submitted_at timestamp.
        5. SUBMISSION DOES NOT APPROVE, QUALIFY, REJECT, OR AWARD THE BID.
        """
        bidder = self._get_bidder_for_user(current_user_id)
        bid = self.db.scalar(select(Bid).where(Bid.id == bid_id))
        if bid is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "BID_NOT_FOUND", "message": "Bid workspace not found."}},
            )

        if bid.bidder_id != bidder.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "FORBIDDEN", "message": "You do not own this bid."}},
            )

        if bid.status == "SUBMITTED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "ALREADY_SUBMITTED", "message": "This bid has already been submitted."}},
            )

        # Require at least one document
        doc_count = self.db.scalar(select(func.count(Document.id)).where(Document.bid_id == bid.id)) or 0
        if doc_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "NO_DOCUMENTS", "message": "Cannot submit bid without any attached proposal or compliance documents."}},
            )

        now = datetime.now(timezone.utc)
        bid.status = "SUBMITTED"
        bid.submitted_at = now
        bid.updated_at = now
        self.db.commit()
        self.db.refresh(bid)

        try:
            AuditService(db=self.db).record_event(
                action="BID_SUBMITTED",
                entity_type="BID",
                entity_id=bid.id,
                user_id=current_user_id,
                details={
                    "bidder_id": str(bidder.id),
                    "tender_id": str(bid.tender_id),
                    "documents_count": doc_count,
                    "submitted_at": now.isoformat(),
                },
                session=self.db,
            )
        except Exception as audit_err:
            logger.warning("Failed to record BID_SUBMITTED audit event: %s", audit_err)

        return BidSubmitResponse(
            id=bid.id,
            status=bid.status,
            submitted_at=bid.submitted_at,
            message="Bid submitted successfully for statutory evaluation.",
        )
