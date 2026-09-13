"""AI extraction schemas package.

Exports document-specific Pydantic output schemas for GST, PAN, and UDYAM.
These schemas are used for validating the structured JSON returned by AI providers.
"""

from app.ai.schemas.gst import GSTExtractionSchema
from app.ai.schemas.pan import PANExtractionSchema
from app.ai.schemas.udyam import UDYAMExtractionSchema

__all__ = [
    "GSTExtractionSchema",
    "PANExtractionSchema",
    "UDYAMExtractionSchema",
]


def get_schema_for_document_type(document_type: str):
    """Return the Pydantic schema class for a given document type.

    Falls back to None for unknown types (caller decides how to handle).
    """
    mapping = {
        "GST": GSTExtractionSchema,
        "PAN": PANExtractionSchema,
        "UDYAM": UDYAMExtractionSchema,
        "VENDOR-GST": GSTExtractionSchema,
        "VENDOR_GST": GSTExtractionSchema,
        "VENDOR-PAN": PANExtractionSchema,
        "VENDOR_PAN": PANExtractionSchema,
    }
    return mapping.get((document_type or "").upper())
