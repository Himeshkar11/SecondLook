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
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.schemas.bid import BidDocumentRead, BidRead, BidSubmitResponse
from app.schemas.bidder_compliance import (
    BidderComplianceHistoryItem,
    BidderComplianceRequirementItem,
    BidderComplianceSummary,
    BidderComplianceViewResponse,
)
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

    def get_bid_compliance(self, current_user_id: UUID, bid_id: UUID) -> BidderComplianceViewResponse:
        """Retrieve factual compliance assessment and deterministic score for a bidder's own bid.

        Security & Privacy Rules:
        1. Validates authenticated bidder ownership (returns HTTP 403 if foreign bid).
        2. Strictly read-only; bidder cannot alter evaluation or requirement outcomes.
        3. Excludes internal officer notes, decisions, and administrative deliberations.
        4. Exposes deterministic score, status, failure/partial explanations, and evidence traces.
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

        disclaimer = (
            "Informational assessment based on currently evaluated requirements. "
            "Final tender decisions are made through the official procurement officer review process. "
            "SecondLook does not approve, qualify, rank, or award tenders."
        )

        # Locate latest compliance evaluation for this bidder and tender
        latest_eval = self.db.scalar(
            select(ComplianceEvaluation)
            .where(
                ComplianceEvaluation.tender_id == bid.tender_id,
                ComplianceEvaluation.bidder_id == bidder.id,
            )
            .order_by(desc(ComplianceEvaluation.completed_at), desc(ComplianceEvaluation.created_at))
        )

        tender = bid.tender
        tender_title = tender.title if tender else None
        tender_ref = tender.reference_number if tender else None

        # Honest un-evaluated state if no evaluation has been run yet
        if latest_eval is None:
            return BidderComplianceViewResponse(
                bid_id=bid.id,
                tender_id=bid.tender_id,
                bidder_id=bidder.id,
                tender_title=tender_title,
                tender_reference_number=tender_ref,
                evaluation_id=None,
                status="NOT_EVALUATED",
                score=None,
                score_formatted="—",
                summary=None,
                requirements=[],
                disclaimer=disclaimer,
                completed_at=None,
                created_at=None,
                message="Compliance evaluation has not started yet. Once procurement officers initiate evaluation of submitted proposals, results and score will appear here.",
            )

        # Compute deterministic compliance score
        summary_dict = latest_eval.summary or {}
        total = summary_dict.get("total_requirements", 0)
        not_applicable = summary_dict.get("not_applicable_count", 0)
        applicable = total - not_applicable
        passed = summary_dict.get("pass_count", 0)

        if applicable > 0:
            score_val = round((passed / applicable) * 100.0, 1)
            score_formatted = f"{score_val}%"
        else:
            score_val = None
            score_formatted = "—"

        summary_obj = BidderComplianceSummary(
            total_requirements=total,
            applicable_count=applicable,
            pass_count=passed,
            fail_count=summary_dict.get("fail_count", 0),
            partial_count=summary_dict.get("partial_count", 0),
            not_verified_count=summary_dict.get("not_verified_count", 0),
            not_applicable_count=not_applicable,
            mandatory_total=summary_dict.get("mandatory_total", 0),
            mandatory_passed=summary_dict.get("mandatory_passed", 0),
            mandatory_failed=summary_dict.get("mandatory_failed", 0),
            mandatory_not_verified=summary_dict.get("mandatory_not_verified", 0),
            optional_total=summary_dict.get("optional_total", 0),
            optional_passed=summary_dict.get("optional_passed", 0),
            optional_failed=summary_dict.get("optional_failed", 0),
            optional_not_verified=summary_dict.get("optional_not_verified", 0),
        )

        # Retrieve requirement evaluation records
        req_evals = self.db.scalars(
            select(RequirementEvaluation).where(RequirementEvaluation.evaluation_id == latest_eval.id)
        ).all()

        req_ids = [re.requirement_id for re in req_evals]
        t_reqs = {}
        if req_ids:
            t_reqs = {
                tr.id: tr
                for tr in self.db.scalars(
                    select(TenderRequirement).where(TenderRequirement.id.in_(req_ids))
                ).all()
            }

        sorted_evals = sorted(
            req_evals,
            key=lambda x: getattr(t_reqs.get(x.requirement_id), "display_order", 999),
        )

        requirement_items: List[BidderComplianceRequirementItem] = []
        for ev in sorted_evals:
            tr = t_reqs.get(ev.requirement_id)
            res_dict = ev.result or {}
            explanation = res_dict.get("explanation") or res_dict.get("summary")

            ev_list = ev.evidence or []
            sources: List[str] = []
            doc_id: Optional[str] = None
            for item in ev_list:
                if isinstance(item, dict):
                    if item.get("source"):
                        sources.append(str(item["source"]))
                    if not doc_id and item.get("document_id"):
                        doc_id = str(item["document_id"])

            unique_sources = sorted(list(set(sources)))
            has_evidence = bool(unique_sources or doc_id)

            st = (ev.status or "NOT_VERIFIED").upper()
            if st == "FAIL":
                guidance = "Review the tender requirement criteria and ensure your submitted documents address all parameters."
            elif st == "PARTIAL":
                guidance = "Additional supporting certificates or clarifying documentation are required to achieve full compliance."
            elif st == "NOT_VERIFIED":
                guidance = "Attach the relevant statutory certificate (e.g. GST, PAN, or MSME) in your bid workspace to enable automated verification."
            elif st == "PASS":
                guidance = "Statutory requirement verified successfully."
            else:
                guidance = None

            requirement_items.append(
                BidderComplianceRequirementItem(
                    requirement_id=ev.requirement_id,
                    requirement_code=tr.code if tr else "REQ",
                    requirement_title=tr.title if tr else "Requirement",
                    requirement_type=tr.type if tr else None,
                    mandatory=tr.mandatory if tr else True,
                    status=st,
                    explanation=explanation,
                    evidence_sources=unique_sources,
                    has_evidence=has_evidence,
                    document_id=doc_id,
                    actionable_guidance=guidance,
                )
            )

        return BidderComplianceViewResponse(
            bid_id=bid.id,
            tender_id=bid.tender_id,
            bidder_id=bidder.id,
            tender_title=tender_title,
            tender_reference_number=tender_ref,
            evaluation_id=latest_eval.id,
            status=latest_eval.status,
            score=score_val,
            score_formatted=score_formatted,
            summary=summary_obj,
            requirements=requirement_items,
            disclaimer=disclaimer,
            completed_at=latest_eval.completed_at.isoformat() if latest_eval.completed_at else None,
            created_at=latest_eval.created_at.isoformat() if latest_eval.created_at else None,
            message=None,
        )

    def get_bid_compliance_history(self, current_user_id: UUID, bid_id: UUID) -> List[BidderComplianceHistoryItem]:
        """Fetch audit history of all evaluation runs for the bidder's own bid."""
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

        records = self.db.scalars(
            select(ComplianceEvaluation)
            .where(
                ComplianceEvaluation.tender_id == bid.tender_id,
                ComplianceEvaluation.bidder_id == bidder.id,
            )
            .order_by(desc(ComplianceEvaluation.created_at))
        ).all()

        history_items: List[BidderComplianceHistoryItem] = []
        for r in records:
            summary = r.summary or {}
            total = summary.get("total_requirements", 0)
            not_app = summary.get("not_applicable_count", 0)
            app = total - not_app
            passed = summary.get("pass_count", 0)
            score = round((passed / app) * 100.0, 1) if app > 0 else None
            score_str = f"{score}%" if score is not None else "—"

            history_items.append(
                BidderComplianceHistoryItem(
                    evaluation_id=r.id,
                    status=r.status,
                    score=score,
                    score_formatted=score_str,
                    total_requirements=total,
                    pass_count=passed,
                    fail_count=summary.get("fail_count", 0),
                    created_at=r.created_at.isoformat() if r.created_at else "",
                    completed_at=r.completed_at.isoformat() if r.completed_at else None,
                )
            )

        return history_items
