"""Document-specific AI extraction output schemas for PAN cards.

All fields are Optional. Fields not found in OCR text must be null.
The AI extractor MUST NOT invent values for missing fields.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PANExtractionSchema(BaseModel):
    """Structured output schema for PAN Card extraction.

    Fields mirror the versioned prompt PAN_EXTRACTION_PROMPT_V1.
    All fields are Optional — absent data is represented as None, not invented.
    """

    pan: Optional[str] = Field(
        None,
        description="PAN (10-character alphanumeric). Null if not found.",
    )
    name: Optional[str] = Field(
        None,
        description="Name of the PAN holder exactly as stated. Null if not found.",
    )
    date_of_birth_or_incorporation: Optional[str] = Field(
        None,
        description=(
            "Date of birth (individuals) or date of incorporation (entities), "
            "normalized to YYYY-MM-DD. Null if not found."
        ),
    )

    model_config = {"extra": "ignore"}
