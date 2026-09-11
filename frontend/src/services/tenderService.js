/**
 * Tender Service
 * Handles API operations for procurement tenders.
 */

import { apiClient } from '../api/client.js';

export async function getTenders(page = 1, pageSize = 20) {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  }).toString();

  return apiClient(`/api/v1/tenders?${query}`);
}

export async function getTenderById(id) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(id)}`);
}
