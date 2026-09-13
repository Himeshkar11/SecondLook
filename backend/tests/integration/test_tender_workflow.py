import uuid

from test_compliance_orchestration import sqlite_session
from app.ai.extractor import StructuredDocumentData
from app.models.document import Document
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.ocr.processor import ExtractedText, OCRProcessor
from app.schemas.compliance import TenderRequirementCreate
from app.services.compliance_service import ComplianceService
from app.workers.worker import DocumentAIWorker, DocumentOCRWorker


class TenderOCR(OCRProcessor):
    def process(self, document):
        return ExtractedText("The bidder shall possess a valid GST registration.")


class TenderAI:
    def extract(self, document_type_or_extracted_text, ocr_text=None):
        return StructuredDocumentData(document_type="TENDER_DOCUMENT", fields={"text_length": len(ocr_text or "")})


def test_complete_tender_document_to_approved_requirement(sqlite_session):
    session, tender_id, bidder_id, user_id = sqlite_session
    tender = session.get(Tender, uuid.UUID(tender_id))
    document = Document(
        id=uuid.uuid4(), tender_id=tender.id, document_type="TENDER_DOCUMENT",
        file_name="eligibility.pdf", storage_path="tenders/eligibility.pdf",
        mime_type="application/pdf", file_size=128, status="QUEUED", ocr_status="QUEUED",
        ai_status="AI_PENDING",
    )
    session.add(document)
    session.commit()

    ocr_job = DocumentOCRWorker(ocr_processor=TenderOCR(), db=session).process_document_by_id(
        str(document.id), content_override=b"tender bytes"
    )
    ai_job = DocumentAIWorker(ai_extractor=TenderAI(), db=session).process_document_by_id(str(document.id))
    assert ocr_job.status == "OCR_COMPLETED"
    assert ai_job.status == "AI_COMPLETED"

    service = ComplianceService(db=session)
    candidates = service.extract_tender_requirements(
        tender_id=tender_id, document_id=str(document.id)
    )
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.status == "AI_SUGGESTED"
    assert candidate.source_document_id == document.id
    assert session.get(Document, document.id).tender_id == tender.id

    approved = service.approve_requirement(str(candidate.id), officer_id=user_id)
    session.expire_all()
    persisted = session.get(TenderRequirement, approved.id)
    assert persisted.status == "APPROVED"
    assert persisted.approved_by == uuid.UUID(user_id)
