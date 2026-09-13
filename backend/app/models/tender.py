import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

tender_bidders = Table(
    "tender_bidders",
    Base.metadata,
    Column("tender_id", UUID(as_uuid=True), ForeignKey("tenders.id"), primary_key=True),
    Column("bidder_id", UUID(as_uuid=True), ForeignKey("bidders.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator: Mapped["User"] = relationship("User", back_populates="tenders")
    bidders: Mapped[list["Bidder"]] = relationship("Bidder", secondary="tender_bidders", back_populates="tenders")
    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="tender", cascade="all, delete-orphan")
    requirements: Mapped[list["TenderRequirement"]] = relationship("TenderRequirement", back_populates="tender", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="tender", cascade="all, delete-orphan")
    compliance_evaluations: Mapped[list["ComplianceEvaluation"]] = relationship("ComplianceEvaluation", back_populates="tender", cascade="all, delete-orphan")
