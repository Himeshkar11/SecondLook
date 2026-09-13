"""Officer Review Service — Task 16.

Orchestrates review lifecycle:
  PENDING → IN_PROGRESS (on create/get)
  IN_PROGRESS → COMPLETED (on complete, with server-side validation)

Decision values are officer-initiated only. The system NEVER automatically
qualifies, disqualifies, rejects, or awards a bidder.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.review.models import OfficerReview, RequirementReview
from app.review.repository import OfficerReviewRepository, RequirementReviewRepository
from app.review.schemas import (
    OFFICER_DECISIONS,
    REQUIREMENT_REVIEW_STATUSES,
    REVIEW_STATUSES,
    ComplianceSummaryRead,
    OfficerReviewRead,
    RequirementResultItem,
    RequirementReviewRead,
    ReviewPayloadResponse,
)
from app.services.audit_service import get_audit_service

logger = logging.getLogger(__name__)


class ReviewValidationError(ValueError):
    """Raised for invalid review state transitions."""
    pass


class ReviewService:
    """Business logic for officer review creation, updates, and completion."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._review_repo = OfficerReviewRepository(db)
        self._req_review_repo = RequirementReviewRepository(db)
        self._audit = get_audit_service(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_evaluation(self, evaluation_id: uuid.UUID) -> ComplianceEvaluation:
        ev = self.db.get(ComplianceEvaluation, evaluation_id)
        if ev is None:
            raise ReviewValidationError(f"Compliance evaluation {evaluation_id} not found.")
        return ev

    def _build_compliance_summary(self, evaluation: ComplianceEvaluation) -> ComplianceSummaryRead:
        """Derive the summary from evaluation.summary JSON (stored by ComplianceService)."""
        raw = evaluation.summary or {}
        return ComplianceSummaryRead(
            total=raw.get("total", 0),
            passed=raw.get("passed", 0),
            failed=raw.get("failed", 0),
            partial=raw.get("partial", 0),
            not_verified=raw.get("not_verified", 0),
            not_applicable=raw.get("not_applicable", 0),
        )

    def _build_requirement_items(
        self,
        evaluation: ComplianceEvaluation,
        review: Optional[OfficerReview],
    ) -> List[RequirementResultItem]:
        """Build per-requirement review items from requirement_evaluations."""
        result_map: Dict[uuid.UUID, RequirementReview] = {}
        if review is not None:
            for rr in review.requirement_reviews:
                result_map[rr.requirement_result_id] = rr

        items: List[RequirementResultItem] = []
        for re in evaluation.requirement_evaluations:
            req: TenderRequirement = re.requirement
            rr = result_map.get(re.id)

            # Extract explanation from stored evidence
            explanation: Optional[str] = None
            evidence_list = re.evidence or []
            if isinstance(evidence_list, list) and evidence_list:
                first = evidence_list[0]
                if isinstance(first, dict):
                    explanation = first.get("explanation")

            rr_read: Optional[RequirementReviewRead] = None
            if rr is not None:
                rr_read = RequirementReviewRead(
                    id=rr.id,
                    review_id=rr.review_id,
                    requirement_result_id=rr.requirement_result_id,
                    review_status=rr.review_status,
                    officer_comment=rr.officer_comment,
                    reviewed_at=rr.reviewed_at,
                    reviewed_by=rr.reviewed_by,
                )

            items.append(
                RequirementResultItem(
                    requirement_result_id=re.id,
                    requirement_id=req.id,
                    requirement_title=req.title,
                    requirement_code=req.code,
                    requirement_type=req.type,
                    mandatory=req.mandatory,
                    compliance_status=re.status,
                    explanation=explanation,
                    rule_results=re.rule_results or [],
                    review=rr_read,
                )
            )
        return items

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_review_payload(self, evaluation_id: uuid.UUID) -> ReviewPayloadResponse:
        """Return the full review payload for a compliance evaluation."""
        ev = self._get_evaluation(evaluation_id)
        review = self._review_repo.get_by_evaluation(evaluation_id)
        summary = self._build_compliance_summary(ev)
        requirements = self._build_requirement_items(ev, review)

        review_read: Optional[OfficerReviewRead] = None
        if review is not None:
            review_read = OfficerReviewRead.model_validate(review)

        return ReviewPayloadResponse(
            evaluation_id=ev.id,
            tender_id=ev.tender_id,
            bidder_id=ev.bidder_id,
            evaluation_status=ev.status,
            summary=summary,
            review=review_read,
            requirements=requirements,
        )

    def create_review(
        self,
        evaluation_id: uuid.UUID,
        reviewer_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
    ) -> ReviewPayloadResponse:
        """Create (or return existing) officer review. Transitions to IN_PROGRESS."""
        ev = self._get_evaluation(evaluation_id)
        existing = self._review_repo.get_by_evaluation(evaluation_id)

        if existing is not None:
            # Idempotent — just return current payload
            return self.get_review_payload(evaluation_id)

        review = self._review_repo.create(evaluation_id, reviewer_id, notes)
        self._review_repo.update_status(review, "IN_PROGRESS")

        # Pre-create NOT_REVIEWED stubs for every requirement result
        for re in ev.requirement_evaluations:
            self._req_review_repo.create(review.id, re.id)

        self.db.commit()

        # Audit
        self._audit.record_event(
            action="OFFICER_REVIEW_STARTED",
            entity_type="officer_review",
            entity_id=review.id,
            user_id=reviewer_id,
            details={"evaluation_id": str(evaluation_id)},
            session=self.db,
        )

        return self.get_review_payload(evaluation_id)

    def update_requirement_review(
        self,
        evaluation_id: uuid.UUID,
        requirement_result_id: uuid.UUID,
        status: str,
        comment: Optional[str],
        reviewer_id: Optional[uuid.UUID] = None,
    ) -> RequirementReviewRead:
        """Mark an individual requirement as REVIEWED or FLAGGED."""
        if status not in REQUIREMENT_REVIEW_STATUSES:
            raise ReviewValidationError(
                f"Invalid review_status '{status}'. Must be one of {REQUIREMENT_REVIEW_STATUSES}."
            )
        if status == "NOT_REVIEWED":
            raise ReviewValidationError("Cannot explicitly set status back to NOT_REVIEWED.")

        review = self._review_repo.get_by_evaluation(evaluation_id)
        if review is None:
            raise ReviewValidationError(
                "No review exists for this evaluation. Create a review first."
            )
        if review.status == "COMPLETED":
            raise ReviewValidationError("Review is already COMPLETED. No further changes allowed.")

        rr = self._req_review_repo.upsert(
            review_id=review.id,
            requirement_result_id=requirement_result_id,
            review_status=status,
            officer_comment=comment,
            reviewed_by=reviewer_id,
        )
        self.db.commit()

        action = "REQUIREMENT_FLAGGED" if status == "FLAGGED" else "REQUIREMENT_REVIEWED"
        self._audit.record_event(
            action=action,
            entity_type="requirement_review",
            entity_id=rr.id,
            user_id=reviewer_id,
            details={
                "evaluation_id": str(evaluation_id),
                "requirement_result_id": str(requirement_result_id),
                "status": status,
                "comment": comment,
            },
            session=self.db,
        )

        return RequirementReviewRead.model_validate(rr)

    def update_decision(
        self,
        evaluation_id: uuid.UUID,
        decision: str,
        notes: Optional[str],
        reviewer_id: Optional[uuid.UUID] = None,
    ) -> OfficerReviewRead:
        """Update the officer decision. Can be updated at any time while IN_PROGRESS."""
        if decision not in OFFICER_DECISIONS:
            raise ReviewValidationError(
                f"Invalid decision '{decision}'. Must be one of {OFFICER_DECISIONS}."
            )

        review = self._review_repo.get_by_evaluation(evaluation_id)
        if review is None:
            raise ReviewValidationError("No review exists. Create a review first.")
        if review.status == "COMPLETED":
            raise ReviewValidationError("Review is already COMPLETED.")

        self._review_repo.update_decision(review, decision, notes)
        self.db.commit()

        if notes:
            self._audit.record_event(
                action="OFFICER_NOTE_ADDED",
                entity_type="officer_review",
                entity_id=review.id,
                user_id=reviewer_id,
                details={"evaluation_id": str(evaluation_id)},
                session=self.db,
            )

        self._audit.record_event(
            action="OFFICER_DECISION_RECORDED",
            entity_type="officer_review",
            entity_id=review.id,
            user_id=reviewer_id,
            details={
                "evaluation_id": str(evaluation_id),
                "decision": decision,
            },
            session=self.db,
        )

        return OfficerReviewRead.model_validate(review)

    def complete_review(
        self,
        evaluation_id: uuid.UUID,
        reviewer_id: Optional[uuid.UUID] = None,
    ) -> ReviewPayloadResponse:
        """Complete the officer review — server-side validation enforced.

        Rules:
        1. The compliance evaluation must be COMPLETED.
        2. All mandatory requirement results must be REVIEWED or FLAGGED.
        3. Officer decision must not be NO_DECISION.
        """
        ev = self._get_evaluation(evaluation_id)

        if ev.status != "COMPLETED":
            raise ReviewValidationError(
                "Cannot complete review: compliance evaluation is not yet COMPLETED "
                f"(current status: {ev.status})."
            )

        review = self._review_repo.get_by_evaluation(evaluation_id)
        if review is None:
            raise ReviewValidationError("No review exists. Create a review first.")
        if review.status == "COMPLETED":
            raise ReviewValidationError("Review is already COMPLETED.")

        if review.decision == "NO_DECISION":
            raise ReviewValidationError(
                "Cannot complete review: an explicit officer decision must be selected "
                "(NO_DECISION is not valid for completion)."
            )

        # Build a set of requirement_result_ids for mandatory requirements
        mandatory_result_ids: set[uuid.UUID] = {
            re.id for re in ev.requirement_evaluations if re.requirement.mandatory
        }

        reviewed_result_ids: set[uuid.UUID] = {
            rr.requirement_result_id
            for rr in review.requirement_reviews
            if rr.review_status in {"REVIEWED", "FLAGGED"}
        }

        unreviewed = mandatory_result_ids - reviewed_result_ids
        if unreviewed:
            raise ReviewValidationError(
                f"Cannot complete review: {len(unreviewed)} mandatory requirement(s) have not been reviewed."
            )

        self._review_repo.update_status(review, "COMPLETED")
        self.db.commit()

        self._audit.record_event(
            action="OFFICER_REVIEW_COMPLETED",
            entity_type="officer_review",
            entity_id=review.id,
            user_id=reviewer_id,
            details={
                "evaluation_id": str(evaluation_id),
                "decision": review.decision,
            },
            session=self.db,
        )

        return self.get_review_payload(evaluation_id)
