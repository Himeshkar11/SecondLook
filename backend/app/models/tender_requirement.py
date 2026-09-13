import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TenderRequirement(Base):
    """Tender statutory / compliance requirement definition (Task 11).

    Requirements belong to a Tender and specify structured deterministic rules
    evaluated by the Compliance Engine against verified evidence.
    """

    __tablename__ = "tender_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="GST")  # GST, PAN, UDYAM, DOCUMENT, etc.
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    rule_config: Mapped[list | dict] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tender: Mapped["Tender"] = relationship("Tender", back_populates="requirements")
    evaluations: Mapped[list["RequirementEvaluation"]] = relationship("RequirementEvaluation", back_populates="requirement", cascade="all, delete-orphan")


class RequirementEvaluation(Base):
    """Individual tender requirement evaluation outcome for a bidder (Task 11).

    Stores factual compliance status (PASS/FAIL/PARTIAL/NOT_VERIFIED/NOT_APPLICABLE),
    rule breakdowns, and traceable evidence links.
    """

    __tablename__ = "requirement_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tender_requirements.id", ondelete="CASCADE"), nullable=False)
    bidder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False)
    tender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_VERIFIED")  # PASS, FAIL, PARTIAL, NOT_VERIFIED, NOT_APPLICABLE
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rule_results: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evaluated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    requirement: Mapped["TenderRequirement"] = relationship("TenderRequirement", back_populates="evaluations")
    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="evaluations")
    tender: Mapped["Tender"] = relationship("Tender")
