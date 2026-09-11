/**
 * Bidder Service
 * Handles API operations for procurement bidders/vendors.
 */

import { apiClient } from '../api/client.js';

export async function getBidders(page = 1, pageSize = 20, tenderId = null) {
  const params = {
    page: String(page),
    page_size: String(pageSize),
  };
  if (tenderId) {
    params.tender_id = tenderId;
  }
  const query = new URLSearchParams(params).toString();
  return apiClient(`/api/v1/bidders?${query}`);
}

export async function getBidderById(id) {
  return apiClient(`/api/v1/bidders/${encodeURIComponent(id)}`);
}

export const getBidder = getBidderById;
