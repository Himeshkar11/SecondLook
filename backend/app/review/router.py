"""FastAPI router for Task 16 Officer Review endpoints.

All endpoints are mounted at:
  /api/v1/compliance/evaluations/{evaluation_id}/review
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.authz.dependencies import require_officer
from app.review.schemas import (
    OfficerDecisionUpdate,
    OfficerReviewCreate,
    OfficerReviewRead,
    RequirementReviewRead,
    RequirementReviewUpdate,
    ReviewPayloadResponse,
)
from app.review.service import ReviewService, ReviewValidationError

logger = logging.getLogger(__name__)

review_router = APIRouter(
    prefix="/api/v1/compliance/evaluations/{evaluation_id}/review",
    tags=["Officer Review"],
)


def _get_service(
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
) -> ReviewService:
    return ReviewService(db)


@review_router.get(
    "",
    response_model=ReviewPayloadResponse,
    summary="Get officer review payload",
    description="Returns the full review payload: evaluation summary, requirement results, and current review state.",
)
def get_review(
    evaluation_id: uuid.UUID,
    service: ReviewService = Depends(_get_service),
) -> ReviewPayloadResponse:
    try:
        return service.get_review_payload(evaluation_id)
    except ReviewValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error fetching review for %s", evaluation_id)
        raise HTTPException(status_code=500, detail=str(exc))


@review_router.post(
    "",
    response_model=ReviewPayloadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start officer review",
    description="Creates a new officer review (or returns existing). Transitions to IN_PROGRESS.",
)
def create_review(
    evaluation_id: uuid.UUID,
    body: OfficerReviewCreate = ...,
    service: ReviewService = Depends(_get_service),
) -> ReviewPayloadResponse:
    try:
        return service.create_review(evaluation_id, body.reviewer_id, body.notes)
    except ReviewValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error creating review for %s", evaluation_id)
        raise HTTPException(status_code=500, detail=str(exc))


@review_router.patch(
    "/requirements/{requirement_result_id}",
    response_model=RequirementReviewRead,
    summary="Review individual requirement",
    description="Mark a requirement result as REVIEWED or FLAGGED, with optional officer comment.",
)
def update_requirement_review(
    evaluation_id: uuid.UUID,
    requirement_result_id: uuid.UUID,
    body: RequirementReviewUpdate,
    service: ReviewService = Depends(_get_service),
) -> RequirementReviewRead:
    try:
        return service.update_requirement_review(
            evaluation_id=evaluation_id,
            requirement_result_id=requirement_result_id,
            status=body.status,
            comment=body.comment,
        )
    except ReviewValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error reviewing requirement %s", requirement_result_id)
        raise HTTPException(status_code=500, detail=str(exc))


@review_router.patch(
    "/decision",
    response_model=OfficerReviewRead,
    summary="Update officer decision",
    description=(
        "Update the officer's overall decision and notes. "
        "Valid decisions: QUALIFIED, NOT_QUALIFIED, REQUIRES_CLARIFICATION, WITHDRAWN, NO_DECISION."
    ),
)
def update_decision(
    evaluation_id: uuid.UUID,
    body: OfficerDecisionUpdate,
    service: ReviewService = Depends(_get_service),
) -> OfficerReviewRead:
    try:
        return service.update_decision(
            evaluation_id=evaluation_id,
            decision=body.decision,
            notes=body.notes,
        )
    except ReviewValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error updating decision for %s", evaluation_id)
        raise HTTPException(status_code=500, detail=str(exc))


@review_router.post(
    "/complete",
    response_model=ReviewPayloadResponse,
    summary="Complete officer review",
    description=(
        "Complete the review. Server-side validates: "
        "(1) evaluation is COMPLETED, "
        "(2) all mandatory requirements are reviewed, "
        "(3) decision is not NO_DECISION."
    ),
)
def complete_review(
    evaluation_id: uuid.UUID,
    service: ReviewService = Depends(_get_service),
) -> ReviewPayloadResponse:
    try:
        return service.complete_review(evaluation_id)
    except ReviewValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error completing review for %s", evaluation_id)
        raise HTTPException(status_code=500, detail=str(exc))
