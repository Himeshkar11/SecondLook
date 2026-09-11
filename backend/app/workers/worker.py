"""Worker execution mechanism for asynchronous verification jobs.

Coordinates retrieving jobs, driving the status lifecycle (QUEUED -> PROCESSING -> COMPLETED/FAILED),
and executing the M15 VerificationPipeline.

The worker contains NO OCR logic, AI prompt logic, rules math, scoring formulas,
risk thresholds, SQL queries, or HTTP calls.
"""

from __future__ import annotations

from typing import Optional

from app.ocr.processor import DocumentInput
from app.verification.pipeline import VerificationPipeline
from app.workers.jobs import JobQueue, JobStatus, VerificationJobRecord


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
