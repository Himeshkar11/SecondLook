"""Repository layer for Task 16 Officer Review models.

Pure DB CRUD — no business logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.review.models import OfficerReview, RequirementReview


class OfficerReviewRepository:
    """CRUD for OfficerReview."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_evaluation(self, evaluation_id: uuid.UUID) -> Optional[OfficerReview]:
        return (
            self.db.query(OfficerReview)
            .filter(OfficerReview.evaluation_id == evaluation_id)
            .first()
        )

    def get_by_id(self, review_id: uuid.UUID) -> Optional[OfficerReview]:
        return self.db.get(OfficerReview, review_id)

    def create(
        self,
        evaluation_id: uuid.UUID,
        reviewer_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
    ) -> OfficerReview:
        review = OfficerReview(
            id=uuid.uuid4(),
            evaluation_id=evaluation_id,
            reviewer_id=reviewer_id,
            status="PENDING",
            decision="NO_DECISION",
            notes=notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(review)
        self.db.flush()
        return review

    def update_status(self, review: OfficerReview, status: str) -> OfficerReview:
        review.status = status
        review.updated_at = datetime.now(timezone.utc)
        if status == "COMPLETED":
            review.completed_at = datetime.now(timezone.utc)
        self.db.flush()
        return review

    def update_decision(
        self, review: OfficerReview, decision: str, notes: Optional[str]
    ) -> OfficerReview:
        review.decision = decision
        if notes is not None:
            review.notes = notes
        review.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return review


class RequirementReviewRepository:
    """CRUD for RequirementReview."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_review_and_result(
        self, review_id: uuid.UUID, requirement_result_id: uuid.UUID
    ) -> Optional[RequirementReview]:
        return (
            self.db.query(RequirementReview)
            .filter(
                RequirementReview.review_id == review_id,
                RequirementReview.requirement_result_id == requirement_result_id,
            )
            .first()
        )

    def list_by_review(self, review_id: uuid.UUID) -> List[RequirementReview]:
        return (
            self.db.query(RequirementReview)
            .filter(RequirementReview.review_id == review_id)
            .all()
        )

    def create(
        self,
        review_id: uuid.UUID,
        requirement_result_id: uuid.UUID,
    ) -> RequirementReview:
        rr = RequirementReview(
            id=uuid.uuid4(),
            review_id=review_id,
            requirement_result_id=requirement_result_id,
            review_status="NOT_REVIEWED",
        )
        self.db.add(rr)
        self.db.flush()
        return rr

    def upsert(
        self,
        review_id: uuid.UUID,
        requirement_result_id: uuid.UUID,
        review_status: str,
        officer_comment: Optional[str],
        reviewed_by: Optional[uuid.UUID] = None,
    ) -> RequirementReview:
        rr = self.get_by_review_and_result(review_id, requirement_result_id)
        if rr is None:
            rr = RequirementReview(
                id=uuid.uuid4(),
                review_id=review_id,
                requirement_result_id=requirement_result_id,
                review_status=review_status,
                officer_comment=officer_comment,
                reviewed_at=datetime.now(timezone.utc),
                reviewed_by=reviewed_by,
            )
            self.db.add(rr)
        else:
            rr.review_status = review_status
            if officer_comment is not None:
                rr.officer_comment = officer_comment
            rr.reviewed_at = datetime.now(timezone.utc)
            rr.reviewed_by = reviewed_by
        self.db.flush()
        return rr
