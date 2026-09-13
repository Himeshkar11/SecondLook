import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bidder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bidders.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="uploaded")
    uploaded_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ocr_status: Mapped[str | None] = mapped_column(String, nullable=True, default="PENDING")
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_status: Mapped[str | None] = mapped_column(String, nullable=True, default="AI_PENDING")
    ai_extraction: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="documents")
    verification_jobs: Mapped[list["VerificationJob"]] = relationship("VerificationJob", back_populates="document")

