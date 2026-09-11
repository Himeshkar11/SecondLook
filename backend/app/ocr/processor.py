"""OCR processor abstractions and demo implementation.

This module defines the provider-agnostic OCR contract.
It does not depend on any specific OCR vendor, external network service, or AI service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


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
    This contract is provider-neutral and is consumed by downstream services (such as AI extraction).
    """

    text: str
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OCRProcessor(ABC):
    """Abstract interface representing SecondLook's OCR capability.

    Future real OCR implementations (e.g. cloud providers, local engines)
    must implement this interface so calling layers remain isolated from vendor details.
    """

    @abstractmethod
    def process(self, document: DocumentInput) -> ExtractedText:
        """Extract text from the given document input.

        Args:
            document: DocumentInput containing document identifiers or content.

        Returns:
            ExtractedText: Standardized extracted text result.
        """
        raise NotImplementedError("OCR processor must implement process(document)")


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
