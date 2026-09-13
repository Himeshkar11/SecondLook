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

from app.config.settings import settings
from app.database.connection import SessionLocal
from app.models.document import Document
from app.ocr.processor import DocumentInput, OCRProcessor, get_ocr_processor
from app.verification.pipeline import VerificationPipeline
from app.workers.jobs import (
    DocumentOCRJobRecord,
    DocumentOCRStatus,
    JobQueue,
    JobStatus,
    VerificationJobRecord,
    document_ocr_queue,
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
    ) -> None:
        self.ocr_processor = ocr_processor if ocr_processor is not None else get_ocr_processor()
        self.queue = queue if queue is not None else document_ocr_queue
        self.db = db
        self.http_client = http_client
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
