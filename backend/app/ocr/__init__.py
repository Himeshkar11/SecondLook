"""OCR module package for SecondLook document processing.

Exports the provider-neutral OCRProcessor interface, data containers,
StandardOCRProcessor, and DemoOCRProcessor implementations.
"""

from app.ocr.processor import (
    DocumentInput,
    ExtractedText,
    OCRProcessor,
    StandardOCRProcessor,
    DemoOCRProcessor,
    get_ocr_processor,
)

__all__ = [
    "DocumentInput",
    "ExtractedText",
    "OCRProcessor",
    "StandardOCRProcessor",
    "DemoOCRProcessor",
    "get_ocr_processor",
]
