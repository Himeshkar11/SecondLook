"""Job models and queue abstraction for asynchronous document processing and verification tasks.

Defines the exact core lifecycle statuses:
- Document OCR statuses: UPLOADED -> QUEUED -> OCR_PROCESSING -> OCR_COMPLETED / OCR_FAILED
- Verification statuses: QUEUED -> PROCESSING -> COMPLETED / FAILED
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.ocr.processor import DocumentInput, ExtractedText
from app.verification.pipeline import VerificationPipelineResult


class JobStatus(str, Enum):
    """Core verification job execution statuses."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentOCRStatus(str, Enum):
    """Controlled OCR processing lifecycle statuses."""

    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    OCR_PROCESSING = "OCR_PROCESSING"
    OCR_COMPLETED = "OCR_COMPLETED"
    OCR_FAILED = "OCR_FAILED"


class InvalidStateTransitionError(RuntimeError):
    """Raised when an illegal job status transition is attempted."""


class VerificationJobRecord(BaseModel):
    """Job container representing an asynchronous verification request."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = Field(..., description="Bidder or vendor identifier")
    document_id: Optional[str] = Field(None, description="Document identifier reference")
    document_input: Optional[DocumentInput] = Field(None, description="Document input payload for the pipeline")
    verification_type: str = Field(default="vendor-compliance", description="Verification type requested")
    provider: str = Field(default="GST", description="Statutory provider token")
    status: JobStatus = Field(default=JobStatus.QUEUED, description="Current lifecycle status")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: Optional[VerificationPipelineResult] = Field(None, description="Pipeline execution result")
    error: Optional[str] = Field(None, description="Failure reason if execution failed")
    attempt_count: int = Field(default=0, ge=0, description="Number of execution attempts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job context metadata")

    def transition_to(self, new_status: JobStatus, error: Optional[str] = None) -> None:
        """Enforce strict status transitions according to the verification job lifecycle."""
        valid_transitions = {
            JobStatus.QUEUED: {JobStatus.PROCESSING},
            JobStatus.PROCESSING: {JobStatus.COMPLETED, JobStatus.FAILED},
            JobStatus.COMPLETED: set(),
            JobStatus.FAILED: set(),
        }

        allowed = valid_transitions.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition job {self.job_id} from {self.status} to {new_status}"
            )

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if error:
            self.error = error


class DocumentOCRJobRecord(BaseModel):
    """Job container representing an asynchronous document OCR processing request."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = Field(..., description="Document identifier")
    bidder_id: str = Field(..., description="Bidder or vendor identifier")
    storage_path: Optional[str] = Field(None, description="Path to file in storage")
    file_name: str = Field(default="document.pdf", description="Original file name")
    mime_type: Optional[str] = Field(default="application/pdf", description="MIME type")
    document_type: str = Field(default="OTHER", description="Document type classification")
    status: DocumentOCRStatus = Field(default=DocumentOCRStatus.QUEUED, description="Lifecycle status")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    result: Optional[ExtractedText] = Field(None, description="OCR extraction result")
    error: Optional[str] = Field(None, description="Failure reason if execution failed")
    attempt_count: int = Field(default=0, ge=0, description="Number of attempts")
    max_retries: int = Field(default=3, ge=0, description="Maximum allowed attempts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")

    def transition_to(self, new_status: DocumentOCRStatus, error: Optional[str] = None) -> None:
        """Enforce strict document OCR status transitions:
        UPLOADED -> QUEUED -> OCR_PROCESSING -> OCR_COMPLETED or OCR_FAILED
        OCR_FAILED -> QUEUED (for retry)
        """
        valid_transitions = {
            DocumentOCRStatus.UPLOADED: {DocumentOCRStatus.QUEUED},
            DocumentOCRStatus.QUEUED: {DocumentOCRStatus.OCR_PROCESSING},
            DocumentOCRStatus.OCR_PROCESSING: {DocumentOCRStatus.OCR_COMPLETED, DocumentOCRStatus.OCR_FAILED},
            DocumentOCRStatus.OCR_COMPLETED: set(),
            DocumentOCRStatus.OCR_FAILED: {DocumentOCRStatus.QUEUED},
        }

        allowed = valid_transitions.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition document OCR job {self.job_id} from {self.status} to {new_status}"
            )

        self.status = new_status
        now_str = datetime.now(timezone.utc).isoformat()
        self.updated_at = now_str
        if new_status == DocumentOCRStatus.OCR_COMPLETED:
            self.completed_at = now_str
        if error:
            self.error = error


class DocumentAIStatus(str, Enum):
    """Controlled AI extraction lifecycle statuses."""

    AI_PENDING = "AI_PENDING"
    AI_PROCESSING = "AI_PROCESSING"
    AI_COMPLETED = "AI_COMPLETED"
    AI_FAILED = "AI_FAILED"


class DocumentAIJobRecord(BaseModel):
    """Job container representing an asynchronous document AI extraction request."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = Field(..., description="Document identifier")
    bidder_id: Optional[str] = Field(None, description="Bidder or vendor identifier")
    document_type: str = Field(default="OTHER", description="Document type classification")
    ocr_text: Optional[str] = Field(None, description="Raw OCR extracted text")
    status: DocumentAIStatus = Field(default=DocumentAIStatus.AI_PENDING, description="Lifecycle status")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Extracted JSON result")
    error: Optional[str] = Field(None, description="Failure reason if execution failed")
    ai_model: Optional[str] = Field(None, description="Model used for extraction")
    prompt_version: Optional[str] = Field(None, description="Prompt version used")
    attempt_count: int = Field(default=0, ge=0, description="Number of attempts")
    max_retries: int = Field(default=2, ge=0, description="Maximum allowed attempts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")

    def transition_to(self, new_status: DocumentAIStatus, error: Optional[str] = None) -> None:
        """Enforce strict document AI status transitions:
        AI_PENDING -> AI_PROCESSING or AI_FAILED
        AI_PROCESSING -> AI_COMPLETED or AI_FAILED
        AI_FAILED -> AI_PENDING (for retry)
        """
        valid_transitions = {
            DocumentAIStatus.AI_PENDING: {DocumentAIStatus.AI_PROCESSING, DocumentAIStatus.AI_FAILED},
            DocumentAIStatus.AI_PROCESSING: {DocumentAIStatus.AI_COMPLETED, DocumentAIStatus.AI_FAILED},
            DocumentAIStatus.AI_COMPLETED: set(),
            DocumentAIStatus.AI_FAILED: {DocumentAIStatus.AI_PENDING},
        }

        allowed = valid_transitions.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition document AI job {self.job_id} from {self.status} to {new_status}"
            )

        self.status = new_status
        now_str = datetime.now(timezone.utc).isoformat()
        self.updated_at = now_str
        if new_status == DocumentAIStatus.AI_COMPLETED:
            self.completed_at = now_str
        if error:
            self.error = error


class JobQueue:
    """In-memory queue for verification, OCR, and AI processing jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Any] = {}
        self._queue: List[str] = []

    def enqueue(self, job: Any) -> Any:
        """Enqueue a new job in initial pending/queued status if not already set."""
        if hasattr(job, "status") and not job.status:
            if isinstance(job, DocumentOCRJobRecord):
                job.status = DocumentOCRStatus.QUEUED
            elif isinstance(job, DocumentAIJobRecord):
                job.status = DocumentAIStatus.AI_PENDING
            else:
                job.status = JobStatus.QUEUED
        self._jobs[job.job_id] = job
        self._queue.append(job.job_id)
        return job

    def dequeue(self) -> Optional[Any]:
        """Retrieve the next pending job in FIFO order."""
        while self._queue:
            job_id = self._queue.pop(0)
            job = self._jobs.get(job_id)
            if job:
                if isinstance(job, DocumentOCRJobRecord) and job.status == DocumentOCRStatus.QUEUED:
                    return job
                if isinstance(job, DocumentAIJobRecord) and job.status == DocumentAIStatus.AI_PENDING:
                    return job
                if isinstance(job, VerificationJobRecord) and job.status == JobStatus.QUEUED:
                    return job
        return None

    def get_job(self, job_id: str) -> Optional[Any]:
        """Fetch a job by ID."""
        return self._jobs.get(job_id)

    def get_document_job(self, document_id: str) -> Optional[DocumentOCRJobRecord]:
        """Fetch an OCR job by document ID."""
        for j in self._jobs.values():
            if isinstance(j, DocumentOCRJobRecord) and j.document_id == document_id:
                return j
        return None

    def get_document_ai_job(self, document_id: str) -> Optional[DocumentAIJobRecord]:
        """Fetch an AI job by document ID."""
        for j in self._jobs.values():
            if isinstance(j, DocumentAIJobRecord) and j.document_id == document_id:
                return j
        return None

    def update_job(self, job: Any) -> None:
        """Update job state in the repository."""
        self._jobs[job.job_id] = job

    def count(self) -> int:
        """Return total tracked jobs."""
        return len(self._jobs)

    def pending_count(self) -> int:
        """Return count of jobs waiting in initial status."""
        count = 0
        for j in self._jobs.values():
            if isinstance(j, DocumentOCRJobRecord) and j.status == DocumentOCRStatus.QUEUED:
                count += 1
            elif isinstance(j, DocumentAIJobRecord) and j.status == DocumentAIStatus.AI_PENDING:
                count += 1
            elif isinstance(j, VerificationJobRecord) and j.status == JobStatus.QUEUED:
                count += 1
        return count


# Global in-memory OCR job queue instance
document_ocr_queue = JobQueue()

# Global in-memory AI extraction job queue instance
document_ai_queue = JobQueue()
