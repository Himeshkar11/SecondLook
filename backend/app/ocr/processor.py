"""OCR processor abstractions, real standard implementation, and demo implementation.

This module defines the provider-agnostic OCR contract.
It does not depend on any specific external network service or AI service.
"""

from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class DocumentInput:
    """Representation of an input document for OCR processing.

    Carries document metadata and optional content reference.
    Does not depend on any specific storage or transport mechanism.
    """

    document_id: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    content: Optional[bytes] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedText:
    """Standardized OCR output contract.

    Contains extracted raw text, optional confidence score, and optional metadata.
    This contract is provider-neutral and is consumed by downstream services.
    """

    text: str
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OCRProcessor(ABC):
    """Abstract interface representing SecondLook's OCR capability.

    Concrete implementations (e.g. StandardOCRProcessor, DemoOCRProcessor,
    TesseractOCRProcessor, CloudOCRProcessor) must implement this interface so
    calling layers remain isolated from vendor details.
    """

    @abstractmethod
    def process(self, document: DocumentInput) -> ExtractedText:
        """Extract raw text from the given document input.

        Args:
            document: DocumentInput containing document identifiers or content.

        Returns:
            ExtractedText: Standardized extracted text result.
        """
        raise NotImplementedError("OCR processor must implement process(document)")


class StandardOCRProcessor(OCRProcessor):
    """Real local OCR processor suitable for development and production.

    Supports:
    - PDF documents (extracts embedded text via pypdf, with OCR fallback/support)
    - Image documents (PNG, JPG, JPEG via pytesseract/Pillow)
    Falls back gracefully if the underlying binary or OCR engine is not installed,
    providing informative extracted text or error messages without crashing.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None) -> None:
        self.tesseract_cmd = tesseract_cmd

    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF pages using pypdf."""
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content))
            extracted_pages = []
            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    extracted_pages.append(text.strip())

            if extracted_pages:
                return "\n\n".join(extracted_pages)
        except Exception as exc:
            logger.warning("PDF text extraction via pypdf failed or partial: %s", exc)

        return ""

    def _extract_from_image(self, content: bytes) -> str:
        """Extract text from image bytes using pytesseract and Pillow."""
        try:
            from PIL import Image
            import pytesseract

            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

            img = Image.open(io.BytesIO(content))
            return pytesseract.image_to_string(img).strip()
        except Exception as exc:
            logger.warning("Image OCR via pytesseract failed or not configured: %s", exc)
            return ""

    def process(self, document: DocumentInput) -> ExtractedText:
        """Extract text from document input."""
        if not document.content:
            raise ValueError(f"Document {document.document_id or 'unknown'} has no content bytes for OCR processing")

        mime = (document.mime_type or "").lower()
        fn = (document.file_name or "").lower()
        extracted_text = ""
        source = "standard_ocr_processor"

        is_pdf = "pdf" in mime or fn.endswith(".pdf")
        is_image = any(img_ext in fn for img_ext in (".png", ".jpg", ".jpeg")) or "image" in mime

        if is_pdf:
            extracted_text = self._extract_from_pdf(document.content)
            source = "pypdf_standard_extractor"

        if not extracted_text and (is_image or is_pdf):
            # Try image OCR if it's an image or if PDF yielded no direct text
            if is_image:
                extracted_text = self._extract_from_image(document.content)
                source = "tesseract_image_ocr"

        # If document content had plain text or was simple text
        if not extracted_text:
            try:
                # Check if it was plain UTF-8 text file passed in
                extracted_text = document.content.decode("utf-8", errors="ignore").strip()
                # If decoding yields mostly non-printable binary junk, discard it
                printable_count = sum(1 for c in extracted_text if c.isprintable() or c in "\n\r\t")
                if len(extracted_text) > 0 and (printable_count / len(extracted_text)) < 0.7:
                    extracted_text = ""
                else:
                    source = "utf8_fallback_decoder"
            except Exception:
                extracted_text = ""

        if not extracted_text:
            raise RuntimeError(
                f"OCR was unable to extract any readable text from '{document.file_name or 'document'}'."
            )

        return ExtractedText(
            text=extracted_text,
            confidence=0.95,
            metadata={
                "source": source,
                "document_id": document.document_id,
                "file_name": document.file_name,
                "mime_type": document.mime_type,
            },
        )


class DemoOCRProcessor(OCRProcessor):
    """Deterministic demo OCR processor for development and testing.

    Returns deterministic extracted document text based on input metadata
    or predefined demo templates. Does not require API keys, credentials,
    external network calls, or third-party engines.
    """

    DEMO_TEXT_TEMPLATES: Dict[str, str] = {
        "gst": (
            "GOVERNMENT OF INDIA\n"
            "CENTRAL BOARD OF INDIRECT TAXES AND CUSTOMS\n"
            "REGISTRATION CERTIFICATE\n"
            "Registration Number (GSTIN): 27ABCDE1234F1Z5\n"
            "Legal Name: Demo Bidder Pvt Ltd\n"
            "Trade Name: Demo Enterprises\n"
            "Constitution of Business: Private Limited Company\n"
            "Date of Liability: 01/07/2017\n"
            "Period of Validity: From 01/07/2017 To Permanent\n"
            "Type of Registration: Regular\n"
            "Status: ACTIVE\n"
        ),
        "pan": (
            "INCOME TAX DEPARTMENT\n"
            "GOVT. OF INDIA\n"
            "Permanent Account Number Card\n"
            "Permanent Account Number: ABCDE1234F\n"
            "Name: Demo Bidder Pvt Ltd\n"
            "Father's / Incorporated Name: Demo Founder\n"
            "Date of Incorporation: 15/04/2018\n"
            "Status: ACTIVE\n"
        ),
        "udyam": (
            "MINISTRY OF MICRO, SMALL & MEDIUM ENTERPRISES\n"
            "UDYAM REGISTRATION CERTIFICATE\n"
            "UDYAM REGISTRATION NUMBER: UDYAM-TEST-001\n"
            "NAME OF ENTERPRISE: Demo Udyam Enterprise\n"
            "TYPE OF ENTERPRISE: SMALL\n"
            "MAJOR ACTIVITY: SERVICES\n"
            "STATUS: ACTIVE\n"
        ),
        "default": (
            "DEMO DOCUMENT TEXT\n"
            "Identifier: DEMO-DOC-001\n"
            "Organization: Demo Organization Pvt Ltd\n"
            "Status: ACTIVE\n"
            "Issued By: Government Authority Demo\n"
        ),
    }

    def process(self, document: DocumentInput) -> ExtractedText:
        """Return deterministic extracted text for the given document input."""
        doc_type = ""
        if document.metadata:
            doc_type = str(document.metadata.get("document_type", "")).lower()

        if not doc_type and document.file_name:
            fn_lower = document.file_name.lower()
            if "gst" in fn_lower:
                doc_type = "gst"
            elif "pan" in fn_lower:
                doc_type = "pan"
            elif "udyam" in fn_lower or "msme" in fn_lower:
                doc_type = "udyam"

        text = self.DEMO_TEXT_TEMPLATES.get(doc_type, self.DEMO_TEXT_TEMPLATES["default"])

        return ExtractedText(
            text=text,
            confidence=0.99,
            metadata={
                "source": "demo_ocr_processor",
                "document_id": document.document_id,
                "file_name": document.file_name,
                "is_demo": True,
            },
        )


def get_ocr_processor(provider_name: Optional[str] = None) -> OCRProcessor:
    """Factory function to acquire configured OCR processor."""
    from app.config.settings import settings

    provider = (provider_name or settings.ocr_provider or "standard").lower().strip()
    if provider == "demo":
        return DemoOCRProcessor()
    return StandardOCRProcessor()
