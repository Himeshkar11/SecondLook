"""AI document extraction interface and deterministic demo implementation.

This module defines the provider-neutral abstraction for extracting structured
compliance data from OCR extracted text.
It does not depend on any specific AI provider or network API client.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.ocr.processor import ExtractedText


class StructuredDocumentData(BaseModel):
    """Normalized structured document data extracted from OCR text.

    Provides core fields required across Indian government procurement / compliance
    documents, along with an extensible `fields` dictionary for provider/document-specific attributes.
    """

    document_type: str = Field(..., description="Classification of document (e.g. GST, PAN, UDYAM, OTHER)")
    document_number: Optional[str] = Field(None, description="Primary registration/identification number (GSTIN, PAN, etc.)")
    legal_name: Optional[str] = Field(None, description="Legal entity name identified on the document")
    registration_status: Optional[str] = Field(None, description="Status stated on the document (e.g. ACTIVE, INACTIVE)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of the extraction (0.0 to 1.0)")
    fields: Dict[str, Any] = Field(default_factory=dict, description="Extensible document-specific key-value pairs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extraction metadata (source, model, etc.)")


class AIExtractor(ABC):
    """Abstract interface for AI document extraction in SecondLook.

    Future real AI extraction implementations (e.g. LLM engines, multimodal processors)
    must implement this interface so calling services remain isolated from vendor details.
    """

    @abstractmethod
    def extract(self, extracted_text: ExtractedText) -> StructuredDocumentData:
        """Extract structured compliance fields from the provided OCR result.

        Args:
            extracted_text: Standardized ExtractedText from an OCRProcessor.

        Returns:
            StructuredDocumentData: Extracted and normalized document data.
        """
        raise NotImplementedError("AI extractor must implement extract(extracted_text)")


class DemoAIExtractor(AIExtractor):
    """Deterministic demo AI extractor for development and testing.

    Parses OCR text deterministically to simulate structured extraction.
    Does not require external network requests, credentials, or API keys.
    """

    def extract(self, extracted_text: ExtractedText) -> StructuredDocumentData:
        """Return deterministic structured document data from ExtractedText."""
        text = extracted_text.text or ""
        text_upper = text.upper()

        if "GSTIN" in text_upper or "GOODS AND SERVICES TAX" in text_upper or "CENTRAL BOARD OF INDIRECT TAXES" in text_upper:
            gstin_match = re.search(r"(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text)
            gstin = gstin_match.group(1) if gstin_match else "27ABCDE1234F1Z5"

            name_match = re.search(r"Legal Name:\s*([^\n]+)", text, re.IGNORECASE)
            legal_name = name_match.group(1).strip() if name_match else "Demo Bidder Pvt Ltd"

            return StructuredDocumentData(
                document_type="GST",
                document_number=gstin,
                legal_name=legal_name,
                registration_status="ACTIVE",
                confidence=0.98,
                fields={
                    "gstin": gstin,
                    "trade_name": "Demo Enterprises",
                    "constitution": "Private Limited Company",
                    "registration_type": "Regular",
                },
                metadata={
                    "source": "demo_ai_extractor",
                    "is_demo": True,
                },
            )

        if "PERMANENT ACCOUNT NUMBER" in text_upper or "INCOME TAX DEPARTMENT" in text_upper:
            pan_match = re.search(r"([A-Z]{5}\d{4}[A-Z]{1})", text)
            pan = pan_match.group(1) if pan_match else "ABCDE1234F"

            name_match = re.search(r"Name:\s*([^\n]+)", text, re.IGNORECASE)
            legal_name = name_match.group(1).strip() if name_match else "Demo Bidder Pvt Ltd"

            return StructuredDocumentData(
                document_type="PAN",
                document_number=pan,
                legal_name=legal_name,
                registration_status="ACTIVE",
                confidence=0.99,
                fields={
                    "pan": pan,
                    "entity_category": "Company",
                },
                metadata={
                    "source": "demo_ai_extractor",
                    "is_demo": True,
                },
            )

        if "UDYAM" in text_upper or "MSME" in text_upper:
            udyam_match = re.search(r"(UDYAM-[A-Z0-9-]+)", text, re.IGNORECASE)
            udyam_num = udyam_match.group(1).upper() if udyam_match else "UDYAM-TEST-001"

            return StructuredDocumentData(
                document_type="UDYAM",
                document_number=udyam_num,
                legal_name="Demo Udyam Enterprise",
                registration_status="ACTIVE",
                confidence=0.97,
                fields={
                    "udyam_number": udyam_num,
                    "enterprise_type": "SMALL",
                    "major_activity": "SERVICES",
                },
                metadata={
                    "source": "demo_ai_extractor",
                    "is_demo": True,
                },
            )

        return StructuredDocumentData(
            document_type="GENERAL_DOCUMENT",
            document_number="DEMO-DOC-001",
            legal_name="Demo Organization Pvt Ltd",
            registration_status="ACTIVE",
            confidence=0.90,
            fields={
                "extracted_lines_count": len(text.splitlines()),
            },
            metadata={
                "source": "demo_ai_extractor",
                "is_demo": True,
            },
        )
