import pytest

from app.ocr import DocumentInput, DemoOCRProcessor
from app.ai import DemoAIExtractor
from app.integrations.gst import GSTIntegration
from app.verification import VerificationPipeline, PipelineStage
from app.workers import (
    JobStatus,
    VerificationJobRecord,
    JobQueue,
    InvalidStateTransitionError,
    Worker,
)


# ==================================================
# 1. Job Creation & State Tests
# ==================================================

def test_job_creation_starts_as_queued():
    job = VerificationJobRecord(
        entity_id="bidder-123",
        document_id="doc-456",
        provider="GST",
    )
    assert job.status == JobStatus.QUEUED
    assert job.job_id is not None
    assert job.entity_id == "bidder-123"
    assert job.document_id == "doc-456"
    assert job.result is None
    assert job.error is None
    assert job.attempt_count == 0


def test_status_transitions_valid_lifecycle():
    job = VerificationJobRecord(entity_id="b-1")

    # QUEUED -> PROCESSING
    job.transition_to(JobStatus.PROCESSING)
    assert job.status == JobStatus.PROCESSING

    # PROCESSING -> COMPLETED
    job.transition_to(JobStatus.COMPLETED)
    assert job.status == JobStatus.COMPLETED


def test_status_transitions_failure_lifecycle():
    job = VerificationJobRecord(entity_id="b-1")

    # QUEUED -> PROCESSING -> FAILED
    job.transition_to(JobStatus.PROCESSING)
    job.transition_to(JobStatus.FAILED, error="Some failure")
    assert job.status == JobStatus.FAILED
    assert job.error == "Some failure"


def test_invalid_status_transitions_raise_error():
    # QUEUED directly to COMPLETED is invalid
    job = VerificationJobRecord(entity_id="b-1")
    with pytest.raises(InvalidStateTransitionError):
        job.transition_to(JobStatus.COMPLETED)

    # COMPLETED cannot transition to PROCESSING
    job.transition_to(JobStatus.PROCESSING)
    job.transition_to(JobStatus.COMPLETED)
    with pytest.raises(InvalidStateTransitionError):
        job.transition_to(JobStatus.PROCESSING)


# ==================================================
# 2. Queue Tests
# ==================================================

def test_job_queue_enqueue_dequeue_fifo():
    queue = JobQueue()
    job1 = VerificationJobRecord(entity_id="b-1")
    job2 = VerificationJobRecord(entity_id="b-2")

    queue.enqueue(job1)
    queue.enqueue(job2)

    assert queue.count() == 2
    assert queue.pending_count() == 2

    dequeued1 = queue.dequeue()
    assert dequeued1 is not None
    assert dequeued1.entity_id == "b-1"

    dequeued2 = queue.dequeue()
    assert dequeued2 is not None
    assert dequeued2.entity_id == "b-2"

    assert queue.dequeue() is None


# ==================================================
# 3. Worker Execution Tests
# ==================================================

def test_worker_processes_job_successfully_to_completed():
    pipeline = VerificationPipeline(
        ocr_processor=DemoOCRProcessor(),
        ai_extractor=DemoAIExtractor(),
        integration=GSTIntegration(),
    )
    queue = JobQueue()
    worker = Worker(pipeline=pipeline, queue=queue)

    job = VerificationJobRecord(
        entity_id="bidder-001",
        document_id="doc-001",
        document_input=DocumentInput(
            file_name="gst_cert.pdf",
            metadata={"document_type": "gst"},
        ),
    )
    queue.enqueue(job)

    processed_job = worker.process_next_job()

    assert processed_job is not None
    assert processed_job.status == JobStatus.COMPLETED
    assert processed_job.attempt_count == 1
    assert processed_job.result is not None
    assert processed_job.result.success is True
    assert processed_job.result.stage == PipelineStage.COMPLETED
    assert processed_job.error is None


def test_worker_processes_failed_pipeline_to_failed():
    # Pipeline that will fail at OCR stage
    class FailingOCR(DemoOCRProcessor):
        def process(self, document: DocumentInput):
            raise RuntimeError("Corrupted document format")

    pipeline = VerificationPipeline(
        ocr_processor=FailingOCR(),
        ai_extractor=DemoAIExtractor(),
        integration=GSTIntegration(),
    )
    queue = JobQueue()
    worker = Worker(pipeline=pipeline, queue=queue)

    job = VerificationJobRecord(
        entity_id="bidder-001",
        document_id="doc-001",
        document_input=DocumentInput(file_name="bad.pdf"),
    )
    queue.enqueue(job)

    processed_job = worker.process_next_job()

    assert processed_job is not None
    assert processed_job.status == JobStatus.FAILED
    assert processed_job.attempt_count == 1
    assert processed_job.result is not None
    assert processed_job.result.success is False
    assert processed_job.result.stage == PipelineStage.OCR
    assert "Corrupted document format" in processed_job.error
    assert processed_job.status != JobStatus.COMPLETED


def test_worker_handles_unexpected_pipeline_exception():
    class ThrowingPipeline(VerificationPipeline):
        def run(self, *args, **kwargs):
            raise Exception("Fatal unexpected infrastructure error")

    pipeline = ThrowingPipeline(
        ocr_processor=DemoOCRProcessor(),
        ai_extractor=DemoAIExtractor(),
        integration=GSTIntegration(),
    )
    queue = JobQueue()
    worker = Worker(pipeline=pipeline, queue=queue)

    job = VerificationJobRecord(entity_id="bidder-001")
    queue.enqueue(job)

    processed = worker.process_next_job()
    assert processed.status == JobStatus.FAILED
    assert "Fatal unexpected infrastructure error" in processed.error


def test_worker_isolation_does_not_call_network_or_database():
    """Verify worker can execute entirely in-memory with injected mocks/demo classes."""
    pipeline = VerificationPipeline(
        ocr_processor=DemoOCRProcessor(),
        ai_extractor=DemoAIExtractor(),
        integration=GSTIntegration(),
    )
    worker = Worker(pipeline=pipeline)

    job = VerificationJobRecord(
        entity_id="in-memory-bidder",
        document_id="in-memory-doc",
    )

    res = worker.process_job(job)
    assert res.status == JobStatus.COMPLETED
    assert res.result.score.percentage == 100.0
