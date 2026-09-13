import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GovernmentVerification(Base):
    """Statutory government verification record (Task 10).

    Preserves full immutable audit history of every verification attempt
    without destroying previous records when re-verifying.
    """

    __tablename__ = "government_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    bidder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # GST, PAN, UDYAM, EPFO, ESIC, etc.
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # demo, etc.
    identifier: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    verification_result: Mapped[str | None] = mapped_column(String(50), nullable=True)  # VERIFIED, MISMATCH, NOT_FOUND, SOURCE_ERROR, CLEAR, LISTED
    government_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    field_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(nullable=False, default=True)
    retrieved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="government_verifications")
    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="government_verifications")
