"""Document-specific AI extraction output schemas for GST certificates.

All fields are Optional. Fields not found in OCR text must be null.
The AI extractor MUST NOT invent values for missing fields.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class GSTExtractionSchema(BaseModel):
    """Structured output schema for GST Certificate extraction.

    Fields mirror the versioned prompt GST_EXTRACTION_PROMPT_V1.
    All fields are Optional — absent data is represented as None, not invented.
    """

    gstin: Optional[str] = Field(
        None,
        description="GSTIN registration number (15-character alphanumeric). Null if not found.",
        pattern=r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$|^$",
    )
    legal_name: Optional[str] = Field(
        None,
        description="Legal name of the registered entity. Null if not found.",
    )
    trade_name: Optional[str] = Field(
        None,
        description="Trade name if different from legal name. Null if not found.",
    )
    registration_date: Optional[str] = Field(
        None,
        description="Registration date normalized to YYYY-MM-DD. Null if not found.",
    )
    status: Optional[str] = Field(
        None,
        description="GST registration status as stated in document (e.g. ACTIVE). Null if not found.",
    )
    address: Optional[str] = Field(
        None,
        description="Registered address. Null if not found.",
    )

    model_config = {"extra": "ignore"}
