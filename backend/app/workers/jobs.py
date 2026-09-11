"""Job models and queue abstraction for asynchronous verification tasks.

Defines the exact core lifecycle statuses (QUEUED -> PROCESSING -> COMPLETED/FAILED),
the VerificationJobRecord container, and an in-memory JobQueue.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from app.ocr.processor import DocumentInput
from app.verification.pipeline import VerificationPipelineResult


class JobStatus(str, Enum):
    """Core verification job execution statuses."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InvalidStateTransitionError(RuntimeError):
    """Raised when an illegal job status transition is attempted."""


class VerificationJobRecord(BaseModel):
    """Job container representing an asynchronous verification request.

    Carries the job identifier, entity/document references, current lifecycle
    status, attempt counter, and the attached VerificationPipelineResult upon completion.
    """

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
        """Enforce strict status transitions according to the job lifecycle:

        QUEUED -> PROCESSING -> COMPLETED
        or
        QUEUED -> PROCESSING -> FAILED
        """
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


class JobQueue:
    """In-memory queue for verification jobs.

    Provides deterministic FIFO scheduling for the M16 skeleton.
    Can be swapped later for a distributed broker without changing the worker.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, VerificationJobRecord] = {}
        self._queue: List[str] = []

    def enqueue(self, job: VerificationJobRecord) -> VerificationJobRecord:
        """Enqueue a new job in QUEUED status."""
        job.status = JobStatus.QUEUED
        self._jobs[job.job_id] = job
        self._queue.append(job.job_id)
        return job

    def dequeue(self) -> Optional[VerificationJobRecord]:
        """Retrieve the next QUEUED job in FIFO order."""
        while self._queue:
            job_id = self._queue.pop(0)
            job = self._jobs.get(job_id)
            if job and job.status == JobStatus.QUEUED:
                return job
        return None

    def get_job(self, job_id: str) -> Optional[VerificationJobRecord]:
        """Fetch a job by ID."""
        return self._jobs.get(job_id)

    def update_job(self, job: VerificationJobRecord) -> None:
        """Update job state in the repository."""
        self._jobs[job.job_id] = job

    def count(self) -> int:
        """Return total tracked jobs."""
        return len(self._jobs)

    def pending_count(self) -> int:
        """Return count of jobs waiting in QUEUED status."""
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.QUEUED)
