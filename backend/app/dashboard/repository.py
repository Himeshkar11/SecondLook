from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.bid import Bid
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.review.models import OfficerReview, RequirementReview


class DashboardRepository:
    """Batch reads used by the dashboard; it never mutates procurement state."""

    def __init__(self, db: Session):
        self.db = db

    def get_tender(self, tender_id: str) -> Optional[Tender]:
        try:
            value = uuid.UUID(tender_id)
            statement = select(Tender).where(Tender.id == value)
        except (ValueError, AttributeError):
            statement = select(Tender).where(Tender.reference_number == tender_id)
        return self.db.execute(
            statement.options(
                joinedload(Tender.bidders),
                joinedload(Tender.requirements),
                joinedload(Tender.bids).joinedload(Bid.bidder),
            )
        ).unique().scalars().first()

    def get_all_tenders(self) -> list[Tender]:
        return list(
            self.db.execute(
                select(Tender)
                .options(
                    joinedload(Tender.bidders),
                    joinedload(Tender.requirements),
                    joinedload(Tender.bids).joinedload(Bid.bidder),
                )
                .order_by(Tender.created_at.desc())
            ).unique().scalars().all()
        )


    def get_evaluations(self, tender_id: uuid.UUID) -> list[ComplianceEvaluation]:
        return list(self.db.execute(
            select(ComplianceEvaluation).where(ComplianceEvaluation.tender_id == tender_id)
        ).scalars().all())

    def get_requirement_evaluations(self, tender_id: uuid.UUID) -> list[RequirementEvaluation]:
        return list(self.db.execute(
            select(RequirementEvaluation).where(RequirementEvaluation.tender_id == tender_id)
        ).scalars().all())

    def get_reviews(self, evaluation_ids: list[uuid.UUID]) -> list[OfficerReview]:
        if not evaluation_ids:
            return []
        return list(self.db.execute(
            select(OfficerReview).where(OfficerReview.evaluation_id.in_(evaluation_ids))
        ).scalars().all())

    def get_requirement_reviews(self, review_ids: list[uuid.UUID]) -> list[RequirementReview]:
        if not review_ids:
            return []
        return list(self.db.execute(
            select(RequirementReview).where(RequirementReview.review_id.in_(review_ids))
        ).scalars().all())
