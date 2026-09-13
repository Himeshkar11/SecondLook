"""Worker execution mechanism for asynchronous verification and document OCR jobs.

Coordinates retrieving jobs, driving the status lifecycle (QUEUED -> PROCESSING -> COMPLETED/FAILED),
and executing document OCR or verification pipelines.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.extractor import (
    AIEmptyOCRError,
    AIExtractionError,
    AIExtractor,
    get_ai_extractor,
)
from app.config.settings import settings
from app.database.connection import SessionLocal
from app.models.document import Document
from app.ocr.processor import DocumentInput, OCRProcessor, get_ocr_processor
from app.verification.pipeline import VerificationPipeline
from app.workers.jobs import (
    DocumentAIJobRecord,
    DocumentAIStatus,
    DocumentOCRJobRecord,
    DocumentOCRStatus,
    DocumentVerificationJobRecord,
    DocumentVerificationStatus,
    JobQueue,
    JobStatus,
    VerificationJobRecord,
    document_ai_queue,
    document_ocr_queue,
    document_verification_queue,
)


logger = logging.getLogger(__name__)


class Worker:
    """Execution worker for verification jobs.

    Delegates actual verification logic to the injected VerificationPipeline
    while managing job state transitions and error capture.
    """

    def __init__(
        self,
        pipeline: VerificationPipeline,
        queue: Optional[JobQueue] = None,
    ) -> None:
        self.pipeline = pipeline
        self.queue = queue if queue is not None else JobQueue()

    def process_job(self, job: VerificationJobRecord) -> VerificationJobRecord:
        """Process a single verification job through the execution lifecycle."""
        # 1. Enforce transition QUEUED -> PROCESSING
        job.transition_to(JobStatus.PROCESSING)
        job.attempt_count += 1
        self.queue.update_job(job)

        # 2. Prepare document input
        doc_input = job.document_input
        if doc_input is None:
            doc_input = DocumentInput(
                document_id=job.document_id,
                file_name=job.metadata.get("file_name", "document.pdf"),
                metadata={"document_type": job.metadata.get("document_type", "gst")},
            )

        # 3. Execute the VerificationPipeline
        try:
            pipeline_result = self.pipeline.run(
                document=doc_input,
                entity_id=job.entity_id,
                document_id=job.document_id,
                verification_type=job.verification_type,
            )

            job.result = pipeline_result

            # 4. Evaluate pipeline outcome
            if pipeline_result.success:
                job.transition_to(JobStatus.COMPLETED)
            else:
                job.transition_to(
                    JobStatus.FAILED,
                    error=pipeline_result.error or f"Pipeline failed at stage {pipeline_result.stage}",
                )
        except Exception as exc:
            # 5. Capture unexpected infrastructure/execution exceptions as FAILED
            job.transition_to(JobStatus.FAILED, error=f"Worker execution exception: {exc}")

        self.queue.update_job(job)
        return job

    def process_next_job(self) -> Optional[VerificationJobRecord]:
        """Fetch and execute the next queued verification job."""
        job = self.queue.dequeue()
        if job is None:
            return None
        return self.process_job(job)


class DocumentOCRWorker:
    """Worker responsible for processing asynchronous document OCR jobs.

    Steps:
    1. Retrieve queued OCR job
    2. Check document status (Idempotency: prevent processing if already PROCESSING or COMPLETED)
    3. Mark document & job as OCR_PROCESSING
    4. Retrieve original document from Supabase Storage (or memory/fallback)
    5. Pass document to OCRProcessor
    6. Receive raw extracted text
    7. Save raw OCR text, status, and completion timestamp to PostgreSQL
    8. Mark status as OCR_COMPLETED
    9. On failure: preserve original file, record safe error info, set OCR_FAILED
    """

    def __init__(
        self,
        ocr_processor: Optional[OCRProcessor] = None,
        queue: Optional[JobQueue] = None,
        db: Optional[Session] = None,
        http_client: Optional[httpx.Client] = None,
        auto_trigger_ai: bool = False,
    ) -> None:
        self.ocr_processor = ocr_processor if ocr_processor is not None else get_ocr_processor()
        self.queue = queue if queue is not None else document_ocr_queue
        self.db = db
        self.http_client = http_client
        self.auto_trigger_ai = auto_trigger_ai
        self.supabase_url = settings.supabase_url.rstrip("/")
        self.supabase_key = settings.supabase_key
        self.bucket = settings.storage_bucket

    def _fetch_from_storage(self, storage_path: str) -> bytes:
        """Download document bytes from Supabase Storage."""
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self.supabase_key}",
            "apikey": self.supabase_key,
        }

        if self.http_client is not None:
            res = self.http_client.get(url, headers=headers)
        else:
            with httpx.Client(timeout=30.0) as client:
                res = client.get(url, headers=headers)

        if res.status_code != 200:
            raise RuntimeError(f"Storage retrieval failed for path '{storage_path}': HTTP {res.status_code}")

        return res.content

    def process_job(self, job: DocumentOCRJobRecord, content_override: Optional[bytes] = None) -> DocumentOCRJobRecord:
        """Process a single document OCR job with idempotency and error handling."""
        # 1. Idempotency check: don't process if already in progress or completed
        if job.status == DocumentOCRStatus.OCR_PROCESSING:
            logger.warning("Job %s for document %s is already in OCR_PROCESSING. Skipping.", job.job_id, job.document_id)
            return job
        if job.status == DocumentOCRStatus.OCR_COMPLETED:
            logger.info("Job %s for document %s is already OCR_COMPLETED. Skipping.", job.job_id, job.document_id)
            return job

        # 2. Transition job to OCR_PROCESSING
        job.transition_to(DocumentOCRStatus.OCR_PROCESSING)
        job.attempt_count += 1
        self.queue.update_job(job)

        session = self.db
        should_close = False
        if session is None and SessionLocal is not None:
            session = SessionLocal()
            should_close = True

        try:
            # 3. Update database status to OCR_PROCESSING
            doc_uuid = uuid.UUID(job.document_id)
            if session is not None:
                doc = session.scalar(select(Document).where(Document.id == doc_uuid))
                if doc:
                    doc.ocr_status = "OCR_PROCESSING"
                    doc.status = "OCR_PROCESSING"
                    session.commit()

            # 4. Fetch content from Supabase Storage or override
            file_bytes = content_override
            if file_bytes is None:
                if job.storage_path:
                    file_bytes = self._fetch_from_storage(job.storage_path)
                else:
                    raise ValueError(f"No storage path or content available for document {job.document_id}")

            # 5. Build DocumentInput and run OCR
            doc_input = DocumentInput(
                document_id=job.document_id,
                file_name=job.file_name,
                mime_type=job.mime_type,
                content=file_bytes,
                metadata={"document_type": job.document_type},
            )

            extracted = self.ocr_processor.process(doc_input)
            job.result = extracted
            job.transition_to(DocumentOCRStatus.OCR_COMPLETED)

            # 6. Save raw OCR text to PostgreSQL
            now = datetime.now(timezone.utc)
            if session is not None:
                doc = session.scalar(select(Document).where(Document.id == doc_uuid))
                if doc:
                    doc.ocr_status = "OCR_COMPLETED"
                    doc.status = "OCR_COMPLETED"
                    doc.ocr_text = extracted.text
                    doc.ocr_error = None
                    doc.ocr_completed_at = now
                    session.commit()

            # 7. Optionally auto-trigger AI extraction if enabled
            if self.auto_trigger_ai:
                try:
                    ai_worker = DocumentAIWorker(db=session)
                    ai_worker.process_document_by_id(job.document_id, ocr_text_override=extracted.text)
                except Exception as ai_exc:
                    logger.warning("Auto AI extraction after OCR failed for %s: %s", job.document_id, ai_exc)

        except Exception as exc:
            error_msg = f"OCR failed: {str(exc)}"
            logger.error("Error processing document %s: %s", job.document_id, exc)
            job.transition_to(DocumentOCRStatus.OCR_FAILED, error=error_msg)

            # Update PostgreSQL to OCR_FAILED safely; preserve original document
            if session is not None:
                try:
                    doc = session.scalar(select(Document).where(Document.id == doc_uuid))
                    if doc:
                        doc.ocr_status = "OCR_FAILED"
                        doc.status = "OCR_FAILED"
                        doc.ocr_error = error_msg
                        session.commit()
                except Exception as db_exc:
                    logger.error("Failed to record OCR failure in DB for %s: %s", job.document_id, db_exc)
                    session.rollback()

        finally:
            self.queue.update_job(job)
            if should_close and session is not None:
                session.close()

        return job

    def process_document_by_id(
        self,
        document_id: str,
        content_override: Optional[bytes] = None,
        max_retries: int = 3,
    ) -> Optional[DocumentOCRJobRecord]:
        """Create or locate job and run processing for a specific document."""
        session = self.db
        should_close = False
        if session is None and SessionLocal is not None:
            session = SessionLocal()
            should_close = True

        try:
            doc_uuid = uuid.UUID(document_id)
            doc = session.scalar(select(Document).where(Document.id == doc_uuid)) if session else None
            if not doc:
                logger.error("Cannot process OCR for nonexistent document %s", document_id)
                return None

            # Check existing job in queue
            job = self.queue.get_document_job(document_id)
            if not job:
                job = DocumentOCRJobRecord(
                    document_id=str(doc.id),
                    bidder_id=str(doc.bidder_id),
                    storage_path=doc.storage_path,
                    file_name=doc.file_name,
                    mime_type=doc.mime_type,
                    document_type=doc.document_type,
                    status=DocumentOCRStatus.QUEUED,
                    max_retries=max_retries,
                )
                self.queue.enqueue(job)
            elif job.status == DocumentOCRStatus.OCR_FAILED:
                # Retry
                job.transition_to(DocumentOCRStatus.QUEUED)

            return self.process_job(job, content_override=content_override)
        finally:
            if should_close and session is not None:
                session.close()


class DocumentAIWorker:
    """Worker responsible for processing asynchronous document AI extraction jobs.

    Steps:
    1. Retrieve queued AI job or process document by ID.
    2. Check document and job status (Idempotency: prevent processing if already PROCESSING or COMPLETED).
    3. Check OCR preconditions:
       - Document must have ocr_status == OCR_COMPLETED.
       - If OCR_FAILED or not OCR_COMPLETED: DO NOT RUN AI -> set AI_FAILED with error.
       - If ocr_text is empty or whitespace: DO NOT RUN AI -> set AI_FAILED with error "AI extraction skipped because OCR text is empty."
    4. Transition job and document to AI_PROCESSING.
    5. Pass document_type and ocr_text to AIExtractor.extract().
    6. Receive structured document data (validated against document schema).
    7. Save extracted JSON, model, prompt version, status AI_COMPLETED, and completion timestamp to PostgreSQL.
    8. On failure: record safe error info, set AI_FAILED.
    """

    def __init__(
        self,
        ai_extractor: Optional[AIExtractor] = None,
        queue: Optional[JobQueue] = None,
        db: Optional[Session] = None,
    ) -> None:
        self.ai_extractor = ai_extractor if ai_extractor is not None else get_ai_extractor()
        self.queue = queue if queue is not None else document_ai_queue
        self.db = db

    def process_job(
        self,
        job: DocumentAIJobRecord,
        ocr_text_override: Optional[str] = None,
        force_retry: bool = False,
    ) -> DocumentAIJobRecord:
        """Process a single document AI extraction job with idempotency and error handling."""
        # 1. Idempotency check: don't process if already in progress or completed
        if not force_retry:
            if job.status == DocumentAIStatus.AI_PROCESSING:
                logger.warning("Job %s for document %s is already in AI_PROCESSING. Skipping.", job.job_id, job.document_id)
                return job
            if job.status == DocumentAIStatus.AI_COMPLETED:
                logger.info("Job %s for document %s is already AI_COMPLETED. Skipping.", job.job_id, job.document_id)
                return job

        session = self.db
        should_close = False
        if session is None and SessionLocal is not None:
            session = SessionLocal()
            should_close = True

        doc_uuid = uuid.UUID(job.document_id)
        try:
            # 2. Check DB record for OCR status & text
            doc = session.scalar(select(Document).where(Document.id == doc_uuid)) if session else None
            ocr_text = ocr_text_override or (doc.ocr_text if doc else job.ocr_text)
            ocr_status = (doc.ocr_status if doc else None) or "PENDING"
            doc_type = (doc.document_type if doc else job.document_type) or "OTHER"

            # 3. Check OCR prerequisite: OCR must be COMPLETED
            if ocr_status != "OCR_COMPLETED":
                error_msg = f"Cannot run AI extraction: OCR is not completed (current OCR status: {ocr_status})"
                logger.warning("Document %s cannot run AI: %s", job.document_id, error_msg)
                job.transition_to(DocumentAIStatus.AI_FAILED, error=error_msg)
                if doc and session:
                    doc.ai_status = "AI_FAILED"
                    doc.ai_error = error_msg
                    session.commit()
                return job

            # 4. Check OCR text is not empty
            if not ocr_text or not ocr_text.strip():
                error_msg = "AI extraction skipped because OCR text is empty."
                logger.warning("Document %s cannot run AI: %s", job.document_id, error_msg)
                job.transition_to(DocumentAIStatus.AI_FAILED, error=error_msg)
                if doc and session:
                    doc.ai_status = "AI_FAILED"
                    doc.ai_error = error_msg
                    session.commit()
                return job

            # 5. Transition job & document to AI_PROCESSING
            job.transition_to(DocumentAIStatus.AI_PROCESSING)
            job.attempt_count += 1
            self.queue.update_job(job)

            if doc and session:
                doc.ai_status = "AI_PROCESSING"
                session.commit()

            # 6. Extract structured data using configured AIExtractor
            extracted_data = self.ai_extractor.extract(doc_type, ocr_text)

            # 7. Save extracted JSON, model, prompt version to PostgreSQL
            now = datetime.now(timezone.utc)
            fields = extracted_data.fields or {}
            job.result = fields
            job.ai_model = extracted_data.ai_model
            job.prompt_version = extracted_data.prompt_version
            job.transition_to(DocumentAIStatus.AI_COMPLETED)

            if doc and session:
                doc.ai_status = "AI_COMPLETED"
                doc.ai_extraction = fields
                doc.ai_error = None
                doc.ai_completed_at = now
                doc.ai_model = extracted_data.ai_model
                doc.ai_prompt_version = extracted_data.prompt_version
                session.commit()

        except Exception as exc:
            error_msg = f"AI extraction failed: {str(exc)}"
            logger.error("Error running AI extraction on document %s: %s", job.document_id, exc)
            job.transition_to(DocumentAIStatus.AI_FAILED, error=error_msg)

            if session is not None:
                try:
                    doc = session.scalar(select(Document).where(Document.id == doc_uuid))
                    if doc:
                        doc.ai_status = "AI_FAILED"
                        doc.ai_error = error_msg
                        session.commit()
                except Exception as db_exc:
                    logger.error("Failed to record AI failure in DB for %s: %s", job.document_id, db_exc)
                    session.rollback()

        finally:
            self.queue.update_job(job)
            if should_close and session is not None:
                session.close()

        return job

    def process_document_by_id(
        self,
        document_id: str,
        ocr_text_override: Optional[str] = None,
        force_retry: bool = False,
    ) -> Optional[DocumentAIJobRecord]:
        """Create or locate AI job and run processing for a specific document."""
        session = self.db
        should_close = False
        if session is None and SessionLocal is not None:
            session = SessionLocal()
            should_close = True

        try:
            doc_uuid = uuid.UUID(document_id)
            doc = session.scalar(select(Document).where(Document.id == doc_uuid)) if session else None
            if not doc:
                logger.error("Cannot process AI for nonexistent document %s", document_id)
                return None

            # Check existing job in queue
            job = self.queue.get_document_ai_job(document_id)
            if not job:
                job = DocumentAIJobRecord(
                    document_id=str(doc.id),
                    bidder_id=str(doc.bidder_id),
                    document_type=doc.document_type,
                    ocr_text=ocr_text_override or doc.ocr_text,
                    status=DocumentAIStatus.AI_PENDING,
                )
                self.queue.enqueue(job)
            elif force_retry or job.status == DocumentAIStatus.AI_FAILED:
                job.transition_to(DocumentAIStatus.AI_PENDING)

            return self.process_job(job, ocr_text_override=ocr_text_override, force_retry=force_retry)
        finally:
            if should_close and session is not None:
                session.close()


class DocumentVerificationWorker:
    """Worker responsible for executing statutory government verification jobs.

    Steps:
    1. Retrieve queued verification job or process document by ID.
    2. Enforce idempotency: prevent processing if already PROCESSING or COMPLETED.
    3. Verify AI extraction prerequisite:
       - AI status must be AI_COMPLETED.
       - Extracted structured data must exist and contain the required identifier.
       - If AI failed or not completed, verification is blocked and transitioned to FAILED.
    4. Transition job to PROCESSING.
    5. Delegate to GovernmentVerificationService.
    6. Transition job to COMPLETED or FAILED based on verification outcome.
    """

    def __init__(
        self,
        verification_service: Optional[Any] = None,
        queue: Optional[JobQueue] = None,
        db: Optional[Session] = None,
    ) -> None:
        from app.services.government_verification_service import GovernmentVerificationService
        self.verification_service = verification_service if verification_service is not None else GovernmentVerificationService(db=db)
        self.queue = queue if queue is not None else document_verification_queue
        self.db = db

    def process_job(
        self,
        job: DocumentVerificationJobRecord,
        force_retry: bool = False,
    ) -> DocumentVerificationJobRecord:
        """Process a single statutory government verification job."""
        if not force_retry:
            if job.status == DocumentVerificationStatus.PROCESSING:
                logger.warning("Job %s for document %s is already in PROCESSING. Skipping.", job.job_id, job.document_id)
                return job
            if job.status == DocumentVerificationStatus.COMPLETED:
                logger.info("Job %s for document %s is already COMPLETED. Skipping.", job.job_id, job.document_id)
                return job

        job.transition_to(DocumentVerificationStatus.PROCESSING)
        job.attempt_count += 1
        self.queue.update_job(job)

        try:
            result = self.verification_service.verify_document(job.document_id, force=force_retry)
            job.result = result
            if result.get("status") == "COMPLETED":
                job.transition_to(DocumentVerificationStatus.COMPLETED)
            else:
                job.transition_to(DocumentVerificationStatus.FAILED, error=result.get("error"))
        except Exception as exc:
            error_msg = f"Verification failed: {str(exc)}"
            logger.error("Error running government verification on document %s: %s", job.document_id, exc)
            job.transition_to(DocumentVerificationStatus.FAILED, error=error_msg)
        finally:
            self.queue.update_job(job)

        return job

    def process_document_by_id(
        self,
        document_id: str,
        force_retry: bool = False,
    ) -> Optional[DocumentVerificationJobRecord]:
        """Create or locate job and run verification for a specific document."""
        session = self.db
        should_close = False
        if session is None and SessionLocal is not None:
            session = SessionLocal()
            should_close = True

        try:
            doc_uuid = uuid.UUID(document_id)
            doc = session.scalar(select(Document).where(Document.id == doc_uuid)) if session else None
            if not doc:
                logger.error("Cannot process verification for nonexistent document %s", document_id)
                return None

            job = self.queue.get_document_verification_job(document_id)
            if not job:
                job = DocumentVerificationJobRecord(
                    document_id=str(doc.id),
                    bidder_id=str(doc.bidder_id),
                    document_type=doc.document_type,
                    status=DocumentVerificationStatus.PENDING,
                )
                self.queue.enqueue(job)
            elif force_retry or job.status == DocumentVerificationStatus.FAILED:
                job.transition_to(DocumentVerificationStatus.PENDING)

            return self.process_job(job, force_retry=force_retry)
        finally:
            if should_close and session is not None:
                session.close()

