/**
 * Bidder Service
 * Handles API operations for procurement bidders/vendors.
 */

import { apiClient } from '../api/client.js';

const bidderProfileCache = {
  data: null,
  promise: null,
  cachedAt: 0,
};

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

export async function getCurrentBidderProfile(forceRefresh = false) {
  const now = Date.now();
  const ttlMs = 30_000;

  if (!forceRefresh && bidderProfileCache.promise && now - bidderProfileCache.cachedAt < ttlMs) {
    return bidderProfileCache.promise;
  }

  bidderProfileCache.promise = apiClient('/api/v1/bidders/me')
    .then((data) => {
      bidderProfileCache.data = data;
      bidderProfileCache.cachedAt = Date.now();
      return data;
    })
    .catch((error) => {
      bidderProfileCache.data = null;
      bidderProfileCache.cachedAt = 0;
      bidderProfileCache.promise = null;
      throw error;
    });

  return bidderProfileCache.promise;
}

export function invalidateBidderProfileCache() {
  bidderProfileCache.data = null;
  bidderProfileCache.promise = null;
  bidderProfileCache.cachedAt = 0;
}

export const getBidder = getBidderById;
