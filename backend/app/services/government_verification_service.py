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

SUPPORTED_VERIFICATION_SOURCES = {
    "GST",
    "PAN",
    "UDYAM",
    "EPFO",
    "ESIC",
    "STARTUP_INDIA",
    "NSIC",
    "MAKE_IN_INDIA",
    "OEM",
    "BLACKLIST",
}


def _extract_source_identifier(source: str, extracted_fields: Dict[str, Any]) -> tuple[str, str]:
    """Extract standard statutory identifier and its key name for a given source."""
    src = source.upper().strip()
    if src == "GST":
        return (extracted_fields.get("gstin") or "").strip().upper(), "gstin"
    elif src == "PAN":
        return (extracted_fields.get("pan") or "").strip().upper(), "pan"
    elif src in ("UDYAM", "MSME"):
        val = (
            extracted_fields.get("udyam_registration_number")
            or extracted_fields.get("udyam_number")
            or extracted_fields.get("registration_number")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "udyam_registration_number"
    elif src == "EPFO":
        val = (
            extracted_fields.get("establishment_code")
            or extracted_fields.get("epfo_number")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "establishment_code"
    elif src == "ESIC":
        val = (
            extracted_fields.get("esic_code")
            or extracted_fields.get("esic_number")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "esic_code"
    elif src == "STARTUP_INDIA":
        val = (
            extracted_fields.get("dpiit_recognition_number")
            or extracted_fields.get("certificate_number")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "dpiit_recognition_number"
    elif src == "NSIC":
        val = (
            extracted_fields.get("certificate_number")
            or extracted_fields.get("nsic_number")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "certificate_number"
    elif src == "MAKE_IN_INDIA":
        val = (
            extracted_fields.get("declaration_id")
            or extracted_fields.get("certificate_number")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "declaration_id"
    elif src == "OEM":
        val = (
            extracted_fields.get("authorization_code")
            or extracted_fields.get("maf_number")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "authorization_code"
    elif src in ("BLACKLIST", "BLACKLISTING", "DEBARMENT"):
        val = (
            extracted_fields.get("legal_name")
            or extracted_fields.get("entity_name")
            or extracted_fields.get("cin")
            or extracted_fields.get("identifier")
            or ""
        )
        return str(val).strip().upper(), "legal_name"
    return (extracted_fields.get("identifier") or "").strip(), "identifier"


def _validate_source_identifier(source: str, identifier: str) -> bool:
    """Validate identifier format per statutory rules."""
    src = source.upper().strip()
    if src == "GST":
        return validate_gstin_format(identifier)
    elif src == "PAN":
        return validate_pan_format(identifier)
    return len(identifier.strip()) >= 3


class VerificationError(Exception):
    """Base error for verification service operations."""


class AIExtractionPrerequisiteError(VerificationError):
    """Raised when AI extraction has not completed successfully."""


class UnsupportedDocumentTypeError(VerificationError):
    """Raised when document type is not in supported verification types."""


class MissingIdentifierError(VerificationError):
    """Raised when the mandatory statutory identifier is missing."""


class InvalidIdentifierFormatError(VerificationError):
    """Raised when the statutory identifier fails format validation."""


class GovernmentVerificationService:
    """Service orchestrating statutory verification across all supported government providers (Task 14)."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def _get_session(self) -> tuple[Session, bool]:
        if self.db is not None:
            return self.db, False
        if SessionLocal is not None:
            return SessionLocal(), True
        raise RuntimeError("No database connection available")

    def verify(
        self,
        source: str,
        identifier: str,
        bidder_id: Optional[str] = None,
        document_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Directly verify an identifier against a government provider without requiring an uploaded document."""
        session, should_close = self._get_session()
        try:
            norm_source = source.strip().upper()
            if norm_source in ("MSME",):
                norm_source = "UDYAM"
            elif norm_source in ("BLACKLISTING", "DEBARMENT"):
                norm_source = "BLACKLIST"

            if norm_source not in SUPPORTED_VERIFICATION_SOURCES:
                raise UnsupportedDocumentTypeError(f"Unsupported verification source: '{source}'")

            clean_id = (identifier or "").strip().upper()
            if not clean_id:
                raise MissingIdentifierError(f"Missing identifier for verification source {norm_source}")

            if not _validate_source_identifier(norm_source, clean_id):
                raise InvalidIdentifierFormatError(f"Identifier '{clean_id}' does not match expected format for {norm_source}")

            b_uuid = uuid.UUID(bidder_id) if bidder_id else None
            d_uuid = uuid.UUID(document_id) if document_id else None

            provider_token = getattr(settings, f"{norm_source.lower()}_provider", "demo") or "demo"
            now = datetime.now(timezone.utc)

            verification_record = GovernmentVerification(
                document_id=d_uuid,
                bidder_id=b_uuid,
                source=norm_source,
                provider=provider_token,
                identifier=clean_id,
                status="PROCESSING",
                is_demo=True,
                created_at=now,
            )
            session.add(verification_record)
            session.commit()
            session.refresh(verification_record)

            provider = get_government_provider(norm_source)
            gov_response = provider.verify(clean_id, data or {})

            complete_time = datetime.now(timezone.utc)
            verification_record.completed_at = complete_time
            verification_record.retrieved_at = complete_time

            if gov_response.status == GovernmentSourceStatus.NOT_FOUND.value:
                verification_record.status = "COMPLETED"
                verification_record.verification_result = OverallVerificationResult.NOT_FOUND.value
                verification_record.field_results = {
                    "identifier": {
                        "document_value": clean_id,
                        "government_value": None,
                        "status": FieldComparisonStatus.MISSING_FROM_SOURCE.value,
                    }
                }
                verification_record.error = gov_response.message or "Identifier not found in government records."

            elif gov_response.status in {GovernmentSourceStatus.ERROR.value, GovernmentSourceStatus.UNAVAILABLE.value}:
                verification_record.status = "FAILED"
                verification_record.verification_result = OverallVerificationResult.SOURCE_ERROR.value
                verification_record.error = gov_response.message or "Government source error or service unavailable."

            elif gov_response.status == GovernmentSourceStatus.FOUND.value:
                gov_data = gov_response.data or {}
                verification_record.government_data = gov_data
                verification_record.status = "COMPLETED"

                if norm_source == "GST":
                    overall_result, field_results = compare_gst_data(data or {}, gov_data)
                    verification_record.verification_result = overall_result.value
                    verification_record.field_results = field_results
                elif norm_source == "PAN":
                    overall_result, field_results = compare_pan_data(data or {}, gov_data)
                    verification_record.verification_result = overall_result.value
                    verification_record.field_results = field_results
                elif norm_source == "BLACKLIST":
                    is_listed = bool(gov_data.get("listed", False))
                    verification_record.verification_result = "LISTED" if is_listed else "CLEAR"
                    verification_record.field_results = {
                        "listed": {
                            "document_value": None,
                            "government_value": is_listed,
                            "status": "MATCH" if not is_listed else "MISMATCH",
                        }
                    }
                else:
                    verification_record.verification_result = "VERIFIED"
                    verification_record.field_results = {
                        k: {
                            "document_value": (data or {}).get(k),
                            "government_value": v,
                            "status": "MATCH" if (data or {}).get(k) == v else "VERIFIED",
                        }
                        for k, v in gov_data.items()
                        if not k.startswith("_")
                    }
            else:
                verification_record.status = "FAILED"
                verification_record.verification_result = OverallVerificationResult.SOURCE_ERROR.value
                verification_record.error = f"Unexpected provider status: {gov_response.status}"

            session.commit()
            session.refresh(verification_record)
            return self._serialize_verification(verification_record)

        except Exception as exc:
            session.rollback()
            logger.error("Error running direct verification for source %s: %s", source, exc)
            raise
        finally:
            if should_close:
                session.close()

    def verify_document(self, document_id: str, force: bool = False) -> Dict[str, Any]:
        """Verify an AI-extracted document against its statutory government provider.

        Supports GST, PAN, UDYAM, EPFO, ESIC, STARTUP_INDIA, NSIC, MAKE_IN_INDIA, OEM, and BLACKLIST.
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
            if raw_type in ("MSME",):
                raw_type = "UDYAM"
            elif raw_type in ("BLACKLISTING", "DEBARMENT"):
                raw_type = "BLACKLIST"

            if raw_type not in SUPPORTED_DOCUMENT_TYPES:
                raise UnsupportedDocumentTypeError(
                    f"Government verification supports {sorted(SUPPORTED_DOCUMENT_TYPES)}. Document type '{raw_type}' is not supported."
                )

            source = raw_type

            # 4. Extract required identifier
            identifier, id_field_name = _extract_source_identifier(source, extracted_fields)
            if not identifier:
                raise MissingIdentifierError(
                    f"Required identifier '{id_field_name}' was not found in extracted document data."
                )

            # 5. Validate identifier format
            if not _validate_source_identifier(source, identifier):
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
            provider_token = getattr(settings, f"{source.lower()}_provider", "demo") or "demo"

            verification_record = GovernmentVerification(
                document_id=doc_uuid,
                bidder_id=doc.bidder_id,
                source=source,
                provider=provider_token,
                identifier=identifier,
                status="PROCESSING",
                verification_result=None,
                is_demo=True,
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
            verification_record.retrieved_at = now

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
                    verification_record.status = "COMPLETED"
                    verification_record.verification_result = overall_result.value
                    verification_record.field_results = field_results
                    doc.verification_status = overall_result.value
                elif source == "PAN":
                    overall_result, field_results = compare_pan_data(extracted_fields, gov_data)
                    verification_record.status = "COMPLETED"
                    verification_record.verification_result = overall_result.value
                    verification_record.field_results = field_results
                    doc.verification_status = overall_result.value
                elif source == "BLACKLIST":
                    is_listed = bool(gov_data.get("listed", False))
                    verification_record.status = "COMPLETED"
                    verification_record.verification_result = "LISTED" if is_listed else "CLEAR"
                    verification_record.field_results = {
                        "listed": {
                            "document_value": None,
                            "government_value": is_listed,
                            "status": "MATCH" if not is_listed else "MISMATCH",
                        }
                    }
                    doc.verification_status = verification_record.verification_result
                else:
                    verification_record.status = "COMPLETED"
                    verification_record.verification_result = "VERIFIED"
                    verification_record.field_results = {
                        k: {
                            "document_value": extracted_fields.get(k),
                            "government_value": v,
                            "status": "MATCH" if extracted_fields.get(k) == v else "VERIFIED",
                        }
                        for k, v in gov_data.items()
                        if not k.startswith("_")
                    }
                    doc.verification_status = "VERIFIED"

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
            "document_id": str(record.document_id) if record.document_id else None,
            "bidder_id": str(record.bidder_id) if record.bidder_id else None,
            "source": record.source,
            "provider": record.provider,
            "identifier": record.identifier,
            "status": record.status,
            "verification_result": record.verification_result,
            "government_data": record.government_data,
            "field_results": record.field_results,
            "error": record.error,
            "is_demo": getattr(record, "is_demo", True),
            "retrieved_at": record.retrieved_at.isoformat() if getattr(record, "retrieved_at", None) else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
        }
