import { apiClient } from '../api/client.js';
import { listTenderDocuments, uploadTenderDocument } from './complianceService.js';

export { listTenderDocuments, uploadTenderDocument };

export function getDocumentProcessing(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}`);
}

export function getDocumentOcr(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ocr`);
}

export function getDocumentAi(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ai`);
}

export function retryDocumentOcr(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ocr/retry`, { method: 'POST' });
}

export function retryDocumentAi(documentId) {
  return apiClient(`/api/v1/documents/${encodeURIComponent(documentId)}/ai/retry`, { method: 'POST' });
}
