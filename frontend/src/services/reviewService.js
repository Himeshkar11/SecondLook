/**
 * reviewService.js — Task 16 Officer Review API clients.
 *
 * Base URL mirrors the existing complianceService.js pattern.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const REVIEW_BASE = (evaluationId) =>
  `${BASE_URL}/api/v1/compliance/evaluations/${evaluationId}/review`;

/**
 * GET /api/v1/compliance/evaluations/{evaluationId}/review
 * Returns the full review payload: summary + requirements + review state.
 */
export async function getReviewPayload(evaluationId) {
  const resp = await fetch(REVIEW_BASE(evaluationId));
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch review (${resp.status})`);
  }
  return resp.json();
}

/**
 * POST /api/v1/compliance/evaluations/{evaluationId}/review
 * Creates (or returns existing) officer review. Body: { reviewer_id?, notes? }
 */
export async function createReview(evaluationId, body = {}) {
  const resp = await fetch(REVIEW_BASE(evaluationId), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create review (${resp.status})`);
  }
  return resp.json();
}

/**
 * PATCH /api/v1/compliance/evaluations/{evaluationId}/review/requirements/{requirementResultId}
 * Mark a requirement as REVIEWED or FLAGGED.
 * Body: { status: "REVIEWED"|"FLAGGED", comment?: string }
 */
export async function updateRequirementReview(evaluationId, requirementResultId, body) {
  const resp = await fetch(
    `${REVIEW_BASE(evaluationId)}/requirements/${requirementResultId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to review requirement (${resp.status})`);
  }
  return resp.json();
}

/**
 * PATCH /api/v1/compliance/evaluations/{evaluationId}/review/decision
 * Update overall officer decision.
 * Body: { decision: string, notes?: string }
 */
export async function updateOfficerDecision(evaluationId, body) {
  const resp = await fetch(`${REVIEW_BASE(evaluationId)}/decision`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update decision (${resp.status})`);
  }
  return resp.json();
}

/**
 * POST /api/v1/compliance/evaluations/{evaluationId}/review/complete
 * Complete the review — server validates completion rules.
 */
export async function completeReview(evaluationId) {
  const resp = await fetch(`${REVIEW_BASE(evaluationId)}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to complete review (${resp.status})`);
  }
  return resp.json();
}
