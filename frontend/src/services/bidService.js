/**
 * Bid Service (Milestone 08)
 * Handles API operations for bidder tender bid workspaces, document attachments, and submission.
 */

import { apiClient } from '../api/client.js';

export async function createOrGetTenderBid(tenderId) {
  return apiClient(`/api/v1/bidder/tenders/${encodeURIComponent(tenderId)}/bids`, {
    method: 'POST',
  });
}

export async function getMyBids() {
  return apiClient('/api/v1/bidder/bids');
}

export async function getMyBidById(bidId) {
  return apiClient(`/api/v1/bidder/bids/${encodeURIComponent(bidId)}`);
}

export async function uploadBidDocument(bidId, formData) {
  return apiClient(`/api/v1/bidder/bids/${encodeURIComponent(bidId)}/documents`, {
    method: 'POST',
    body: formData,
  });
}

export async function submitBid(bidId) {
  return apiClient(`/api/v1/bidder/bids/${encodeURIComponent(bidId)}/submit`, {
    method: 'POST',
  });
}

export async function retryDocumentOcr(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ocr/retry`, {
    method: 'POST',
  });
}

export async function retryDocumentAi(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ai/retry`, {
    method: 'POST',
  });
}

export async function verifyDocument(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/verify`, {
    method: 'POST',
  });
}

export async function getDocumentAccess(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/access`);
}
