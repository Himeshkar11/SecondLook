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
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="APPROVED")  # DRAFT, AI_SUGGESTED, UNDER_REVIEW, APPROVED, REJECTED, ARCHIVED
    rule_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # STATUS_EQUALS, FIELD_EQUALS, etc.
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rule_config: Mapped[list | dict] = mapped_column(JSON, nullable=False, default=list)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tender: Mapped["Tender"] = relationship("Tender", back_populates="requirements")
    source_document: Mapped["Document | None"] = relationship("Document", foreign_keys=[source_document_id])
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])
    evaluations: Mapped[list["RequirementEvaluation"]] = relationship("RequirementEvaluation", back_populates="requirement", cascade="all, delete-orphan")


class ComplianceEvaluation(Base):
    """Container representing a single complete compliance evaluation run (Task 13).

    Preserves full evaluation history with a unique UUID evaluation_id.
    Each run evaluates all approved tender requirements against resolved bidder evidence.
    """

    __tablename__ = "compliance_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    bidder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tender: Mapped["Tender"] = relationship("Tender", back_populates="compliance_evaluations")
    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="compliance_evaluations")
    requirement_evaluations: Mapped[list["RequirementEvaluation"]] = relationship(
        "RequirementEvaluation", back_populates="evaluation", cascade="all, delete-orphan"
    )


class RequirementEvaluation(Base):
    """Individual tender requirement evaluation outcome for a bidder (Task 11 & Task 13).

    Stores factual compliance status (PASS/FAIL/PARTIAL/NOT_VERIFIED/NOT_APPLICABLE),
    rule breakdowns, and traceable evidence links. References evaluation_id for audit history.
    """

    __tablename__ = "requirement_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("compliance_evaluations.id", ondelete="CASCADE"), nullable=True)
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
    evaluation: Mapped["ComplianceEvaluation | None"] = relationship("ComplianceEvaluation", back_populates="requirement_evaluations")
