import pytest

from app.ocr import (
    DocumentInput,
    ExtractedText,
    OCRProcessor,
    DemoOCRProcessor,
)
from app.ai import (
    AIExtractor,
    DemoAIExtractor,
    StructuredDocumentData,
    ExtractionPromptTemplate,
)


# ==================================================
# M13 — OCR Tests
# ==================================================

def test_m13_ocr_interface_instantiation():
    processor = DemoOCRProcessor()
    assert isinstance(processor, OCRProcessor)


def test_m13_demo_ocr_returns_deterministic_extracted_text():
    processor = DemoOCRProcessor()
    doc_input = DocumentInput(
        document_id="doc-123",
        file_name="vendor_gst_certificate.pdf",
        mime_type="application/pdf",
        metadata={"document_type": "gst"},
    )
    result = processor.process(doc_input)

    assert isinstance(result, ExtractedText)
    assert "27ABCDE1234F1Z5" in result.text
    assert "Demo Bidder Pvt Ltd" in result.text
    assert result.confidence == 0.99
    assert result.metadata["source"] == "demo_ocr_processor"
    assert result.metadata["is_demo"] is True


def test_m13_ocr_does_not_require_network_or_api_keys():
    processor = DemoOCRProcessor()
    doc = DocumentInput(file_name="sample.pdf")
    res = processor.process(doc)
    assert res.text
    assert isinstance(res.text, str)


# ==================================================
# M14 — AI Extraction Tests
# ==================================================

def test_m14_ai_interface_instantiation():
    extractor = DemoAIExtractor()
    assert isinstance(extractor, AIExtractor)


def test_m14_demo_ai_accepts_ocr_output_and_returns_structured_data():
    extractor = DemoAIExtractor()
    extracted_text = ExtractedText(
        text=(
            "Registration Number (GSTIN): 27ABCDE1234F1Z5\n"
            "Legal Name: Demo Bidder Pvt Ltd\n"
            "Status: ACTIVE\n"
        )
    )

    structured_data = extractor.extract(extracted_text)

    assert isinstance(structured_data, StructuredDocumentData)
    assert structured_data.document_type == "GST"
    assert structured_data.document_number == "27ABCDE1234F1Z5"
    assert structured_data.legal_name == "Demo Bidder Pvt Ltd"
    assert structured_data.registration_status == "ACTIVE"
    assert structured_data.fields["gstin"] == "27ABCDE1234F1Z5"
    assert structured_data.metadata["is_demo"] is True


def test_m14_demo_ai_pan_extraction():
    extractor = DemoAIExtractor()
    pan_text = ExtractedText(
        text=(
            "INCOME TAX DEPARTMENT\n"
            "Permanent Account Number: ABCDE1234F\n"
            "Name: Demo Bidder Pvt Ltd\n"
            "Status: ACTIVE\n"
        )
    )

    structured = extractor.extract(pan_text)
    assert structured.document_type == "PAN"
    assert structured.document_number == "ABCDE1234F"
    assert structured.legal_name == "Demo Bidder Pvt Ltd"
    assert structured.registration_status == "ACTIVE"


def test_m14_prompt_template_exists_and_formats():
    prompt = ExtractionPromptTemplate.build_prompt(
        ocr_text="Some document text",
        expected_type="GST",
    )
    assert "system" in prompt
    assert "user" in prompt
    assert "Some document text" in prompt["user"]
    assert "GST" in prompt["user"]
    assert len(prompt["system"]) > 0


# ==================================================
# Pipeline Composition Test
# ==================================================

def test_ocr_to_ai_pipeline_composition():
    """Verify Document -> DemoOCRProcessor -> ExtractedText -> DemoAIExtractor -> StructuredDocumentData."""
    ocr_processor: OCRProcessor = DemoOCRProcessor()
    ai_extractor: AIExtractor = DemoAIExtractor()

    # Step 1: Document input
    doc = DocumentInput(
        document_id="pipeline-doc-001",
        file_name="gst_cert.pdf",
        mime_type="application/pdf",
        metadata={"document_type": "gst"},
    )

    # Step 2: OCR Process
    extracted_text: ExtractedText = ocr_processor.process(doc)
    assert isinstance(extracted_text, ExtractedText)
    assert "27ABCDE1234F1Z5" in extracted_text.text

    # Step 3: AI Extract
    structured_data: StructuredDocumentData = ai_extractor.extract(extracted_text)
    assert isinstance(structured_data, StructuredDocumentData)
    assert structured_data.document_type == "GST"
    assert structured_data.document_number == "27ABCDE1234F1Z5"
    assert structured_data.legal_name == "Demo Bidder Pvt Ltd"
    assert structured_data.registration_status == "ACTIVE"
