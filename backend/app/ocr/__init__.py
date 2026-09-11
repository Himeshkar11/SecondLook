"""OCR module package for SecondLook document processing.

Exports the provider-neutral OCRProcessor interface, data containers,
and DemoOCRProcessor implementation.
"""

from app.ocr.processor import (
    DocumentInput,
    ExtractedText,
    OCRProcessor,
    DemoOCRProcessor,
)

__all__ = [
    "DocumentInput",
    "ExtractedText",
    "OCRProcessor",
    "DemoOCRProcessor",
]
