"""Statutory Government Verification Service (Task 10).

Orchestrates verification of AI-extracted document data against statutory government sources (GST & PAN).
Strictly decoupled from compliance, qualification, risk, or tender scoring logic.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import SessionLocal
from app.integrations.base import GovernmentSourceStatus
from app.integrations.comparison import (
    FieldComparisonStatus,
    OverallVerificationResult,
    compare_gst_data,
    compare_pan_data,
)
from app.integrations.registry import get_government_provider
from app.integrations.validation import validate_gstin_format, validate_pan_format
from app.models.document import Document
from app.models.government_verification import GovernmentVerification

logger = logging.getLogger(__name__)

SUPPORTED_DOCUMENT_TYPES = {"GST", "PAN"}


class VerificationError(Exception):
    """Base error for verification service operations."""


class AIExtractionPrerequisiteError(VerificationError):
    """Raised when AI extraction has not completed successfully."""


class UnsupportedDocumentTypeError(VerificationError):
    """Raised when document type is not GST or PAN."""


class MissingIdentifierError(VerificationError):
    """Raised when the mandatory statutory identifier is missing."""


class InvalidIdentifierFormatError(VerificationError):
    """Raised when the statutory identifier fails format validation."""


class GovernmentVerificationService:
    """Service orchestrating statutory verification against GST and PAN providers."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def _get_session(self) -> tuple[Session, bool]:
        if self.db is not None:
            return self.db, False
        if SessionLocal is not None:
            return SessionLocal(), True
        raise RuntimeError("No database connection available")

    def verify_document(self, document_id: str, force: bool = False) -> Dict[str, Any]:
        """Verify an AI-extracted document against its statutory government provider.

        Steps:
        1. Validate document exists.
        2. Ensure AI extraction exists and is completed.
        3. Ensure document type is supported (GST or PAN).
        4. Extract required identifier; ensure it is present.
        5. Validate identifier format.
        6. Enforce idempotency: skip if already PROCESSING.
        7. Query statutory provider.
        8. Run deterministic field comparison.
        9. Persist immutable verification record to PostgreSQL (Supabase).
        10. Update document verification_status.
        """
        session, should_close = self._get_session()
        try:
            doc_uuid = uuid.UUID(document_id)
            doc = session.scalar(select(Document).where(Document.id == doc_uuid))
            if not doc:
                raise ValueError(f"Document {document_id} not found")

            # 2. Check AI prerequisite
            ai_status = (doc.ai_status or "").upper()
            if ai_status != "AI_COMPLETED":
                raise AIExtractionPrerequisiteError(
                    f"AI extraction must be completed before government verification. Current status: {ai_status or 'PENDING'}"
                )

            extracted_fields = doc.ai_extraction or {}
            if not isinstance(extracted_fields, dict) or not extracted_fields:
                raise AIExtractionPrerequisiteError(
                    "AI extraction result is empty or invalid. Cannot perform government verification."
                )

            # 3. Check document type
            raw_type = (doc.document_type or "").upper().strip()
            if raw_type not in SUPPORTED_DOCUMENT_TYPES:
                raise UnsupportedDocumentTypeError(
                    f"Government verification only supports GST and PAN documents. Document type '{raw_type}' is not supported."
                )

            source = raw_type

            # 4. Extract required identifier
            if source == "GST":
                identifier = (extracted_fields.get("gstin") or "").strip().upper()
                id_field_name = "gstin"
            else:  # PAN
                identifier = (extracted_fields.get("pan") or "").strip().upper()
                id_field_name = "pan"

            if not identifier:
                raise MissingIdentifierError(
                    f"Required identifier '{id_field_name}' was not found in extracted document data."
                )

            # 5. Validate identifier format
            if source == "GST":
                is_valid_format = validate_gstin_format(identifier)
            else:
                is_valid_format = validate_pan_format(identifier)

            if not is_valid_format:
                raise InvalidIdentifierFormatError(
                    f"Identifier '{identifier}' does not match standard {source} format."
                )

            # 6. Idempotency: Check if already processing
            if not force:
                active_job = session.scalar(
                    select(GovernmentVerification)
                    .where(
                        GovernmentVerification.document_id == doc_uuid,
                        GovernmentVerification.status == "PROCESSING",
                    )
                    .order_by(desc(GovernmentVerification.created_at))
                    .limit(1)
                )
                if active_job:
                    logger.info("Verification for document %s is already PROCESSING. Returning existing record.", document_id)
                    return self._serialize_verification(active_job)

            # Create new historical verification record
            provider_token = (
                settings.gst_provider if source == "GST" else settings.pan_provider
            ) or "demo"

            verification_record = GovernmentVerification(
                document_id=doc_uuid,
                bidder_id=doc.bidder_id,
                source=source,
                provider=provider_token,
                identifier=identifier,
                status="PROCESSING",
                verification_result=None,
                created_at=datetime.now(timezone.utc),
            )
            session.add(verification_record)
            doc.verification_status = "PROCESSING"
            session.commit()
            session.refresh(verification_record)

            # 7. Select provider and call verify
            provider = get_government_provider(source)
            gov_response = provider.verify(identifier, extracted_fields)

            now = datetime.now(timezone.utc)
            verification_record.completed_at = now

            # 8. Compare outcomes
            if gov_response.status == GovernmentSourceStatus.NOT_FOUND.value:
                verification_record.status = "COMPLETED"
                verification_record.verification_result = OverallVerificationResult.NOT_FOUND.value
                verification_record.field_results = {
                    id_field_name: {
                        "document_value": identifier,
                        "government_value": None,
                        "status": FieldComparisonStatus.MISSING_FROM_SOURCE.value,
                    }
                }
                verification_record.error = gov_response.message or "Identifier not found in government records."
                doc.verification_status = OverallVerificationResult.NOT_FOUND.value

            elif gov_response.status in {GovernmentSourceStatus.ERROR.value, GovernmentSourceStatus.UNAVAILABLE.value}:
                verification_record.status = "FAILED"
                verification_record.verification_result = OverallVerificationResult.SOURCE_ERROR.value
                verification_record.error = gov_response.message or "Government source error or service unavailable."
                doc.verification_status = OverallVerificationResult.SOURCE_ERROR.value

            elif gov_response.status == GovernmentSourceStatus.FOUND.value:
                gov_data = gov_response.data or {}
                verification_record.government_data = gov_data

                if source == "GST":
                    overall_result, field_results = compare_gst_data(extracted_fields, gov_data)
                else:
                    overall_result, field_results = compare_pan_data(extracted_fields, gov_data)

                verification_record.status = "COMPLETED"
                verification_record.verification_result = overall_result.value
                verification_record.field_results = field_results
                doc.verification_status = overall_result.value

            else:
                verification_record.status = "FAILED"
                verification_record.verification_result = OverallVerificationResult.SOURCE_ERROR.value
                verification_record.error = f"Unexpected provider status: {gov_response.status}"
                doc.verification_status = OverallVerificationResult.SOURCE_ERROR.value

            session.commit()
            session.refresh(verification_record)
            return self._serialize_verification(verification_record)

        except Exception as exc:
            session.rollback()
            logger.error("Error running verification on document %s: %s", document_id, exc)
            raise
        finally:
            if should_close:
                session.close()

    def get_document_verification(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve verification details and history for a document."""
        session, should_close = self._get_session()
        try:
            doc_uuid = uuid.UUID(document_id)
            doc = session.scalar(select(Document).where(Document.id == doc_uuid))
            if not doc:
                return None

            records = session.scalars(
                select(GovernmentVerification)
                .where(GovernmentVerification.document_id == doc_uuid)
                .order_by(desc(GovernmentVerification.created_at))
            ).all()

            latest = records[0] if records else None

            return {
                "document_id": str(doc.id),
                "document_type": doc.document_type,
                "ai_status": doc.ai_status,
                "verification_status": doc.verification_status or (latest.verification_result if latest else "PENDING"),
                "latest_verification": self._serialize_verification(latest) if latest else None,
                "history": [self._serialize_verification(r) for r in records],
            }
        finally:
            if should_close:
                session.close()

    @staticmethod
    def _serialize_verification(record: Optional[GovernmentVerification]) -> Optional[Dict[str, Any]]:
        if record is None:
            return None
        return {
            "id": str(record.id),
            "document_id": str(record.document_id),
            "bidder_id": str(record.bidder_id),
            "source": record.source,
            "provider": record.provider,
            "identifier": record.identifier,
            "status": record.status,
            "verification_result": record.verification_result,
            "government_data": record.government_data,
            "field_results": record.field_results,
            "error": record.error,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
        }
