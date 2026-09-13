import uuid

from test_compliance_orchestration import sqlite_session
from app.ai.extractor import StructuredDocumentData
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.ocr.processor import ExtractedText, OCRProcessor
from app.schemas.compliance import TenderRequirementCreate
from app.services.compliance_service import ComplianceService
from app.services.government_verification_service import GovernmentVerificationService
from app.workers.worker import DocumentAIWorker, DocumentOCRWorker


class BidderOCR(OCRProcessor):
    def process(self, document):
        return ExtractedText("GSTIN 29ABCDE1234F1Z5")


class BidderAI:
    def extract(self, document_type_or_extracted_text, ocr_text=None):
        return StructuredDocumentData(
            document_type="GST",
            fields={"gstin": "29ABCDE1234F1Z5", "legal_name": "Apex Global Technologies Pvt Ltd"},
        )


def test_bidder_document_to_government_evidence(sqlite_session):
    session, tender_id, bidder_id, user_id = sqlite_session
    tender = session.get(Tender, uuid.UUID(tender_id))
    bidder = session.get(Bidder, uuid.UUID(bidder_id))
    tender.bidders.append(bidder)
    document = Document(
        id=uuid.uuid4(), bidder_id=bidder.id, tender_id=tender.id, document_type="GST",
        file_name="gst.pdf", storage_path="bidder/gst.pdf", mime_type="application/pdf",
        file_size=64, status="QUEUED", ocr_status="QUEUED", ai_status="AI_PENDING",
    )
    session.add(document)
    session.commit()

    ocr_job = DocumentOCRWorker(ocr_processor=BidderOCR(), db=session).process_document_by_id(
        str(document.id), content_override=b"gst bytes"
    )
    ai_job = DocumentAIWorker(ai_extractor=BidderAI(), db=session).process_document_by_id(str(document.id))
    assert ocr_job.status == "OCR_COMPLETED"
    assert ai_job.status == "AI_COMPLETED"

    verification = GovernmentVerificationService(db=session).verify_document(str(document.id))
    assert verification["status"] == "COMPLETED"
    assert session.query(GovernmentVerification).filter_by(document_id=document.id).count() == 1

    requirement = ComplianceService(db=session).create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            title="Active GST", type="GST", rule_type="STATUS_EQUALS",
            rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
        ),
        user_id=user_id,
    )
    ComplianceService(db=session).approve_requirement(str(requirement.id), officer_id=user_id)
    evaluation = ComplianceService(db=session).run_compliance_evaluation(tender_id, bidder_id)
    assert evaluation.requirements[0].evidence
    assert evaluation.requirements[0].evidence[0]["source"] == "GST"
    assert evaluation.requirements[0].tender_id == uuid.UUID(tender_id)
