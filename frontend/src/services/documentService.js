/**
 * Document Service
 * Handles API operations for bidder compliance and tender documents.
 */

import { apiClient } from '../api/client.js';

export async function getBidderDocuments(bidderId, page = 1, pageSize = 50) {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  }).toString();
  return apiClient(`/api/v1/bidders/${encodeURIComponent(bidderId)}/documents?${query}`);
}

export async function getAllDocuments(bidderId = null, page = 1, pageSize = 50) {
  const params = {
    page: String(page),
    page_size: String(pageSize),
  };
  if (bidderId) {
    params.bidder_id = bidderId;
  }
  const query = new URLSearchParams(params).toString();
  return apiClient(`/api/v1/documents?${query}`);
}

export async function uploadDocument(bidderId, file, documentType) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  return apiClient(`/api/v1/bidders/${encodeURIComponent(bidderId)}/documents`, {
    method: 'POST',
    body: formData,
  });
}

export async function getDocument(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}`);
}

export async function getDocumentAccess(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/access`);
}

export async function getDocumentOCR(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ocr`);
}

export async function retryDocumentOCR(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ocr/retry`, {
    method: 'POST',
  });
}

export async function getDocumentAI(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ai`);
}

export async function retryDocumentAI(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ai/retry`, {
    method: 'POST',
  });
}
