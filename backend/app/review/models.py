"""SQLAlchemy models for Task 16 Officer Review Layer.

OfficerReview  — one review per compliance evaluation (enforced by unique index).
RequirementReview — per-requirement review record within a review.

These models are read-side companions to the existing ComplianceEvaluation and
RequirementEvaluation models. They do NOT touch the compliance engine results.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OfficerReview(Base):
    """Officer Review record associated with exactly one ComplianceEvaluation (Task 16).

    Status lifecycle: PENDING → IN_PROGRESS → COMPLETED
    Decision values (officer-only): NO_DECISION | QUALIFIED | NOT_QUALIFIED |
                                     REQUIRES_CLARIFICATION | WITHDRAWN
    """

    __tablename__ = "officer_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    decision: Mapped[str] = mapped_column(String(50), nullable=False, default="NO_DECISION")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    requirement_reviews: Mapped[list["RequirementReview"]] = relationship(
        "RequirementReview", back_populates="review", cascade="all, delete-orphan"
    )


class RequirementReview(Base):
    """Per-requirement review record within an OfficerReview (Task 16).

    Status values: NOT_REVIEWED | REVIEWED | FLAGGED
    Each record links to exactly one RequirementEvaluation row.
    """

    __tablename__ = "requirement_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("officer_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirement_evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_REVIEWED")
    officer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    review: Mapped["OfficerReview"] = relationship("OfficerReview", back_populates="requirement_reviews")
