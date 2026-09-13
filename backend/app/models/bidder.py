import uuid

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Bidder(Base):
    __tablename__ = "bidders"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_bidders_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    legal_name: Mapped[str] = mapped_column(String, nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String, nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String, nullable=True)
    pan_number: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="bidder_profile")
    tenders: Mapped[list["Tender"]] = relationship("Tender", secondary="tender_bidders", back_populates="bidders")
    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="bidder", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="bidder")
    verification_jobs: Mapped[list["VerificationJob"]] = relationship("VerificationJob", back_populates="bidder")
    government_verifications: Mapped[list["GovernmentVerification"]] = relationship("GovernmentVerification", back_populates="bidder", cascade="all, delete-orphan")
    evaluations: Mapped[list["RequirementEvaluation"]] = relationship("RequirementEvaluation", back_populates="bidder", cascade="all, delete-orphan")
    compliance_evaluations: Mapped[list["ComplianceEvaluation"]] = relationship("ComplianceEvaluation", back_populates="bidder", cascade="all, delete-orphan")
