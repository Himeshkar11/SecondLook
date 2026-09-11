"""Provider-neutral prompt templates for document information extraction.

This module defines prompt instructions for extracting structured compliance fields
from raw OCR text. It is completely independent of specific AI providers or model vendors.
"""

from typing import Dict, Optional


class ExtractionPromptTemplate:
    """Standardized prompt templates for document extraction tasks."""

    SYSTEM_INSTRUCTION = (
        "You are an expert document compliance extraction engine. "
        "Your task is to analyze the provided raw OCR text and extract structured "
        "information into a standard format without hallucinations. "
        "Only extract fields present in the text. Return fields such as document_type, "
        "document_number, legal_name, registration_status, and any other relevant attributes."
    )

    BASE_USER_TEMPLATE = (
        "Document Context / Expected Type: {expected_type}\n\n"
        "--- BEGIN RAW OCR TEXT ---\n"
        "{ocr_text}\n"
        "--- END RAW OCR TEXT ---\n\n"
        "Extract all available key compliance attributes in structured form."
    )

    @classmethod
    def build_prompt(cls, ocr_text: str, expected_type: Optional[str] = None) -> Dict[str, str]:
        """Build provider-neutral prompt dictionary with system instruction and user prompt.

        Args:
            ocr_text: Raw OCR extracted text string.
            expected_type: Optional hint regarding expected document type (e.g. 'GST', 'PAN').

        Returns:
            Dict containing 'system' and 'user' prompt texts.
        """
        return {
            "system": cls.SYSTEM_INSTRUCTION,
            "user": cls.BASE_USER_TEMPLATE.format(
                expected_type=expected_type or "General Compliance Document",
                ocr_text=ocr_text.strip(),
            ),
        }
