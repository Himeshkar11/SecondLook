/**
 * Compliance Service (Task 11 & Task 12)
 * Handles statutory tender requirements, AI requirement suggestions, officer approval workflows,
 * and factual compliance evaluation.
 * Note: Compliance evaluations represent objective statutory requirement status
 * and do not constitute final bidder procurement awards or rejections.
 */

import { apiClient } from '../api/client.js';

export async function getTenderRequirements(tenderId, status = null) {
  const url = status
    ? `/api/v1/tenders/${encodeURIComponent(tenderId)}/requirements?status=${encodeURIComponent(status)}`
    : `/api/v1/tenders/${encodeURIComponent(tenderId)}/requirements`;
  return apiClient(url);
}

export async function getTenderRequirement(requirementId) {
  return apiClient(`/api/v1/tender-requirements/${encodeURIComponent(requirementId)}`);
}

export async function createTenderRequirement(tenderId, payload) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/requirements`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function extractTenderRequirements(tenderId, { text, document_id }) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/requirements/extract`, {
    method: 'POST',
    body: JSON.stringify({ text, document_id }),
  });
}

export async function updateTenderRequirement(requirementId, payload) {
  return apiClient(`/api/v1/tender-requirements/${encodeURIComponent(requirementId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function approveTenderRequirement(requirementId, officerId = null) {
  return apiClient(`/api/v1/tender-requirements/${encodeURIComponent(requirementId)}/approve`, {
    method: 'POST',
    body: JSON.stringify({ officer_id: officerId }),
  });
}

export async function rejectTenderRequirement(requirementId, reason = null) {
  return apiClient(`/api/v1/tender-requirements/${encodeURIComponent(requirementId)}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function uploadTenderDocument(tenderId, file, documentType = 'TENDER_DOCUMENT') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/documents`, {
    method: 'POST',
    body: formData,
  });
}

export async function listTenderDocuments(tenderId) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/documents`);
}

export async function getBidderCompliance(bidderId, tenderId) {
  const query = new URLSearchParams({ tender_id: tenderId }).toString();
  return apiClient(`/api/v1/bidders/${encodeURIComponent(bidderId)}/compliance?${query}`);
}

export async function evaluateBidderCompliance(bidderId, tenderId) {
  return apiClient(`/api/v1/bidders/${encodeURIComponent(bidderId)}/compliance/evaluate`, {
    method: 'POST',
    body: JSON.stringify({ tender_id: tenderId }),
  });
}

/**
 * Task 13 Multi-Source Compliance Pipeline & Orchestration APIs
 */

export async function runComplianceEvaluation(tenderId, bidderId) {
  return apiClient(
    `/api/v1/tenders/${encodeURIComponent(tenderId)}/bidders/${encodeURIComponent(bidderId)}/compliance/evaluate`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    }
  );
}

export async function getComplianceEvaluation(evaluationId) {
  return apiClient(`/api/v1/compliance/evaluations/${encodeURIComponent(evaluationId)}`);
}

export async function getComplianceEvaluationsHistory(tenderId, bidderId) {
  return apiClient(
    `/api/v1/tenders/${encodeURIComponent(tenderId)}/bidders/${encodeURIComponent(bidderId)}/compliance/evaluations`
  );
}

/**
 * Task 15 Evidence Traceability & Audit Trail APIs
 */

export async function getEvaluationEvidenceTraces(evaluationId) {
  return apiClient(`/api/v1/compliance/evaluations/${encodeURIComponent(evaluationId)}/evidence`);
}

export async function getEvaluationAuditEvents(evaluationId) {
  return apiClient(`/api/v1/compliance/evaluations/${encodeURIComponent(evaluationId)}/audit`);
}

export async function getRequirementEvidenceTrace(requirementId, bidderId = null) {
  const query = bidderId ? `?bidder_id=${encodeURIComponent(bidderId)}` : '';
  return apiClient(`/api/v1/requirements/${encodeURIComponent(requirementId)}/evidence${query}`);
}

export async function getDocumentAccessUrl(documentId, expiresIn = 3600) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/access?expires_in=${expiresIn}`);
}

export async function listAuditEvents(params = {}) {
  const query = new URLSearchParams(params).toString();
  return apiClient(`/api/v1/audit/events${query ? `?${query}` : ''}`);
}
