"""AI document extraction interface, DemoAIExtractor, and factory.

Defines the provider-neutral abstraction for extracting structured information
from OCR-extracted text. The application never depends directly on a specific
AI vendor. Only OCR text is ever passed to extractors — no PDF binary, no
Supabase credentials, no application secrets.

No AI/LLM calls are made by this module. All real provider calls live in
backend/app/ai/providers/.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Controlled AI lifecycle status values
# ---------------------------------------------------------------------------

class AIExtractionStatus:
    """Controlled constants for AI extraction lifecycle states."""

    AI_PENDING = "AI_PENDING"
    AI_PROCESSING = "AI_PROCESSING"
    AI_COMPLETED = "AI_COMPLETED"
    AI_FAILED = "AI_FAILED"


# ---------------------------------------------------------------------------
# Non-retryable vs retryable exception types
# ---------------------------------------------------------------------------

class AIExtractionError(RuntimeError):
    """Non-retryable AI extraction failure (e.g. malformed JSON, schema invalid)."""


class AIProviderRetryableError(RuntimeError):
    """Retryable provider-level failure (timeout, rate limit, 503, connection)."""


class AIEmptyOCRError(AIExtractionError):
    """Raised when OCR text is empty or whitespace-only. Never retried."""


# ---------------------------------------------------------------------------
# Result contract
# ---------------------------------------------------------------------------

class StructuredDocumentData(BaseModel):
    """Normalized structured document data extracted from OCR text.

    Represents the output of an AIExtractor.extract() call.
    Fields are deliberately minimal at the top level — document-specific
    fields live in the `fields` dict keyed by their document schema.

    IMPORTANT: This result NEVER contains compliance decisions, risk scores,
    or verification verdicts. It only contains extracted information.
    """

    document_type: str = Field(..., description="Document type: GST, PAN, UDYAM, OTHER")
    fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document-specific extracted key-value pairs (null for unavailable fields)",
    )
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0.0–1.0)")
    ai_model: Optional[str] = Field(None, description="Model used for extraction (e.g. provider model name)")
    prompt_version: Optional[str] = Field(None, description="Prompt version used (e.g. GST_V1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extraction metadata")

    # Convenience top-level accessors kept for backward compatibility with existing tests
    document_number: Optional[str] = Field(None, description="Primary identifier (GSTIN, PAN, etc.)")
    legal_name: Optional[str] = Field(None, description="Legal entity name")
    registration_status: Optional[str] = Field(None, description="Registration status stated in document")


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class AIExtractor(ABC):
    """Abstract provider-neutral AI extraction interface for SecondLook.

    All concrete implementations (DemoAIExtractor, OpenRouterAIExtractor, etc.)
    must implement this interface so the DocumentAIWorker remains isolated from
    vendor-specific details.
    """

    @abstractmethod
    def extract(
        self,
        document_type_or_extracted_text: Any,
        ocr_text: Optional[str] = None,
    ) -> StructuredDocumentData:
        """Extract structured information from raw OCR text.

        Args:
            document_type_or_extracted_text: Document type string (e.g. "GST", "PAN")
                OR an ExtractedText instance (for backward compatibility).
            ocr_text: Raw OCR-extracted text string. Required if document_type string is passed.

        Returns:
            StructuredDocumentData with extracted fields. Missing fields are null.

        Raises:
            AIEmptyOCRError: If ocr_text is empty/whitespace.
            AIExtractionError: For non-retryable extraction failures.
            AIProviderRetryableError: For retryable provider failures.
        """
        raise NotImplementedError("AIExtractor must implement extract(document_type, ocr_text)")


# ---------------------------------------------------------------------------
# Demo (deterministic, no API key required)
# ---------------------------------------------------------------------------

class DemoAIExtractor(AIExtractor):
    """Deterministic demo AI extractor for development and testing.

    Parses OCR text deterministically using regex patterns to simulate
    structured extraction. Never makes network requests. Never invents values —
    fields not found in OCR text are returned as null.

    This extractor must be usable without any environment variables or API keys.
    """

    def extract(
        self,
        document_type_or_extracted_text: Any,
        ocr_text: Optional[str] = None,
    ) -> StructuredDocumentData:
        """Return deterministic structured document data from OCR text."""
        # Unpack arguments for backward and forward compatibility
        if ocr_text is None:
            if hasattr(document_type_or_extracted_text, "text"):
                text = document_type_or_extracted_text.text or ""
                metadata = getattr(document_type_or_extracted_text, "metadata", {}) or {}
                document_type = metadata.get("document_type") or "OTHER"
            else:
                text = str(document_type_or_extracted_text or "")
                document_type = "OTHER"
        else:
            document_type = str(document_type_or_extracted_text or "OTHER")
            text = ocr_text or ""

        if not text or not text.strip():
            raise AIEmptyOCRError("AI extraction skipped because OCR text is empty.")

        text = text.strip()
        text_upper = text.upper()
        doc_type_upper = (document_type or "").upper()

        # ── GST extraction ──────────────────────────────────────────────────
        is_gst = (
            doc_type_upper in ("GST", "VENDOR-GST", "VENDOR_GST")
            or "GSTIN" in text_upper
            or "GOODS AND SERVICES TAX" in text_upper
            or "CENTRAL BOARD OF INDIRECT TAXES" in text_upper
            or "GST CERTIFICATE" in text_upper
        )
        if is_gst:
            return self._extract_gst(text)

        # ── PAN extraction ──────────────────────────────────────────────────
        is_pan = (
            doc_type_upper == "PAN"
            or "PERMANENT ACCOUNT NUMBER" in text_upper
            or "INCOME TAX DEPARTMENT" in text_upper
            or "PAN CARD" in text_upper
        )
        if is_pan:
            return self._extract_pan(text)

        # ── UDYAM extraction ────────────────────────────────────────────────
        is_udyam = (
            doc_type_upper in ("UDYAM", "MSME")
            or "UDYAM" in text_upper
            or "MSME" in text_upper
        )
        if is_udyam:
            return self._extract_udyam(text)

        # ── Generic fallback ────────────────────────────────────────────────
        return StructuredDocumentData(
            document_type=document_type or "OTHER",
            fields={"extracted_lines_count": len(text.splitlines())},
            confidence=0.50,
            ai_model=None,
            prompt_version=None,
            metadata={"source": "demo_ai_extractor", "is_demo": True},
        )

    # ── GST ─────────────────────────────────────────────────────────────────

    def _extract_gst(self, text: str) -> StructuredDocumentData:
        """Extract GST certificate fields from OCR text. Returns null for missing fields."""
        gstin = self._find_gstin(text)
        legal_name = self._find_field(text, [r"Legal\s+Name\s*[:\-]?\s*([^\n]+)", r"LEGAL\s+NAME\s*[:\-]?\s*([^\n]+)"])
        trade_name = self._find_field(text, [r"Trade\s+Name\s*[:\-]?\s*([^\n]+)", r"TRADE\s+NAME\s*[:\-]?\s*([^\n]+)"])
        status = self._find_field(text, [r"Status\s*[:\-]?\s*([A-Z]+)", r"Registration\s+Status\s*[:\-]?\s*([A-Z]+)"])
        reg_date = self._find_date(text, [r"Registration\s+Date\s*[:\-]?\s*([\d/\-]+)"])
        address = self._find_field(text, [r"Address\s*[:\-]?\s*([^\n]+)"])

        fields = {
            "gstin": gstin,
            "legal_name": legal_name,
            "trade_name": trade_name,
            "registration_date": self._normalize_date(reg_date),
            "status": status,
            "address": address,
        }

        return StructuredDocumentData(
            document_type="GST",
            document_number=gstin,
            legal_name=legal_name,
            registration_status=status,
            fields=fields,
            confidence=0.95,
            ai_model=None,
            prompt_version="GST_V1",
            metadata={"source": "demo_ai_extractor", "is_demo": True},
        )

    # ── PAN ─────────────────────────────────────────────────────────────────

    def _extract_pan(self, text: str) -> StructuredDocumentData:
        """Extract PAN card fields from OCR text. Returns null for missing fields."""
        pan = self._find_pan(text)
        name = self._find_field(text, [r"Name\s*[:\-]?\s*([^\n]+)"])
        dob = self._find_date(text, [r"Date\s+of\s+Birth\s*[:\-]?\s*([\d/\-]+)", r"DOB\s*[:\-]?\s*([\d/\-]+)"])
        doi = self._find_date(text, [r"Date\s+of\s+Incorporation\s*[:\-]?\s*([\d/\-]+)", r"DOI\s*[:\-]?\s*([\d/\-]+)"])
        status = self._find_field(text, [r"Status\s*[:\-]?\s*([A-Z]+)"])

        fields = {
            "pan": pan,
            "name": name,
            "date_of_birth_or_incorporation": self._normalize_date(dob or doi),
        }

        return StructuredDocumentData(
            document_type="PAN",
            document_number=pan,
            legal_name=name,
            registration_status=status,
            fields=fields,
            confidence=0.97,
            ai_model=None,
            prompt_version="PAN_V1",
            metadata={"source": "demo_ai_extractor", "is_demo": True},
        )

    # ── UDYAM ────────────────────────────────────────────────────────────────

    def _extract_udyam(self, text: str) -> StructuredDocumentData:
        """Extract UDYAM registration fields from OCR text. Returns null for missing fields."""
        udyam_number = self._find_udyam(text)
        enterprise_name = self._find_field(text, [r"Enterprise\s+Name\s*[:\-]?\s*([^\n]+)", r"Name\s+of\s+Enterprise\s*[:\-]?\s*([^\n]+)"])
        enterprise_type = self._find_field(text, [r"Enterprise\s+Type\s*[:\-]?\s*([^\n]+)", r"Type\s*[:\-]?\s*(MICRO|SMALL|MEDIUM)"])
        major_activity = self._find_field(text, [r"Major\s+Activity\s*[:\-]?\s*([^\n]+)", r"Activity\s*[:\-]?\s*(MANUFACTURING|SERVICES|TRADING)"])

        fields = {
            "udyam_number": udyam_number,
            "enterprise_name": enterprise_name,
            "enterprise_type": enterprise_type,
            "major_activity": major_activity,
        }

        return StructuredDocumentData(
            document_type="UDYAM",
            document_number=udyam_number,
            legal_name=enterprise_name,
            registration_status=None,
            fields=fields,
            confidence=0.95,
            ai_model=None,
            prompt_version="UDYAM_V1",
            metadata={"source": "demo_ai_extractor", "is_demo": True},
        )

    # ── Private regex helpers ─────────────────────────────────────────────────

    def _find_gstin(self, text: str) -> Optional[str]:
        """Extract GSTIN — returns None if not found (never invented)."""
        m = re.search(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b", text)
        return m.group(1) if m else None

    def _find_pan(self, text: str) -> Optional[str]:
        """Extract PAN — returns None if not found (never invented)."""
        m = re.search(r"\b([A-Z]{5}\d{4}[A-Z])\b", text)
        return m.group(1) if m else None

    def _find_udyam(self, text: str) -> Optional[str]:
        """Extract UDYAM registration number — returns None if not found."""
        m = re.search(r"\b(UDYAM-[A-Z]{2}-\d{2}-\d+)\b", text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
        m2 = re.search(r"\b(UDYAM-[A-Z0-9-]+)\b", text, re.IGNORECASE)
        return m2.group(1).upper() if m2 else None

    def _find_field(self, text: str, patterns: list) -> Optional[str]:
        """Try each pattern; return first match stripped, or None."""
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                return val if val else None
        return None

    def _find_date(self, text: str, patterns: list) -> Optional[str]:
        """Try each date pattern; return raw matched string or None."""
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _normalize_date(self, raw: Optional[str]) -> Optional[str]:
        """Normalize date to YYYY-MM-DD if recognizable, else return as-is or None."""
        if not raw:
            return None
        # DD/MM/YYYY or DD-MM-YYYY
        m = re.match(r"^(\d{2})[/\-](\d{2})[/\-](\d{4})$", raw)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        # Already YYYY-MM-DD
        m2 = re.match(r"^\d{4}-\d{2}-\d{2}$", raw)
        if m2:
            return raw
        return raw


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def get_ai_extractor(provider_name: Optional[str] = None) -> AIExtractor:
    """Factory: return the configured AIExtractor instance.

    Returns DemoAIExtractor when:
    - provider_name is "demo"
    - AI_PROVIDER setting is "demo" or unset
    - OPENROUTER_API_KEY is not configured

    Returns OpenRouterAIExtractor when:
    - provider_name is "openrouter"
    - AI_PROVIDER setting is "openrouter" AND OPENROUTER_API_KEY is set

    Never raises; always falls back to DemoAIExtractor.
    """
    from app.config.settings import settings

    provider = (provider_name or settings.ai_provider or "demo").lower().strip()

    if provider == "openrouter" and settings.openrouter_api_key:
        try:
            from app.ai.providers.openrouter import OpenRouterAIExtractor
            return OpenRouterAIExtractor()
        except Exception as exc:
            logger.warning("Failed to initialize OpenRouterAIExtractor, falling back to Demo: %s", exc)

    return DemoAIExtractor()
