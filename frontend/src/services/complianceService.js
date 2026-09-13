/**
 * Compliance Service (Task 11)
 * Handles statutory tender requirements and factual compliance evaluation.
 * Note: Compliance evaluations represent objective statutory requirement status
 * and do not constitute final bidder procurement awards or rejections.
 */

import { apiClient } from '../api/client.js';

export async function getTenderRequirements(tenderId) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/requirements`);
}

export async function createTenderRequirement(tenderId, payload) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/requirements`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
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
