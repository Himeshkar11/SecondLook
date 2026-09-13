"""Document-specific AI extraction output schemas for UDYAM registrations.

All fields are Optional. Fields not found in OCR text must be null.
The AI extractor MUST NOT invent values for missing fields.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class UDYAMExtractionSchema(BaseModel):
    """Structured output schema for UDYAM Registration Certificate extraction.

    Fields mirror the versioned prompt UDYAM_EXTRACTION_PROMPT_V1.
    All fields are Optional — absent data is represented as None, not invented.
    """

    udyam_number: Optional[str] = Field(
        None,
        description="UDYAM registration number (format: UDYAM-XX-00-0000000). Null if not found.",
    )
    enterprise_name: Optional[str] = Field(
        None,
        description="Name of the registered enterprise. Null if not found.",
    )
    enterprise_type: Optional[str] = Field(
        None,
        description="Enterprise classification: MICRO, SMALL, or MEDIUM. Null if not found.",
    )
    major_activity: Optional[str] = Field(
        None,
        description="Major activity: MANUFACTURING, SERVICES, or TRADING. Null if not found.",
    )

    model_config = {"extra": "ignore"}
