import { apiClient } from '../api/client.js';

export function getTenderDashboard(tenderId) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/dashboard`);
}

export function getTenderDashboardRequirements(tenderId) {
  return apiClient(`/api/v1/tenders/${encodeURIComponent(tenderId)}/dashboard/requirements`);
}

export function getOfficerDashboardOverview() {
  return apiClient('/api/v1/officer/dashboard');
}
