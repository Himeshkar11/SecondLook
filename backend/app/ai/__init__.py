"""AI module package for SecondLook document processing.

Exports the provider-neutral AIExtractor interface, StructuredDocumentData schema,
DemoAIExtractor implementation, and ExtractionPromptTemplate.
"""

from app.ai.extractor import (
    AIExtractor,
    DemoAIExtractor,
    StructuredDocumentData,
)
from app.ai.prompts import ExtractionPromptTemplate

__all__ = [
    "AIExtractor",
    "DemoAIExtractor",
    "StructuredDocumentData",
    "ExtractionPromptTemplate",
]
