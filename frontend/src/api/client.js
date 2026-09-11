/**
 * SecondLook API HTTP Client
 * Centralized API client for communicating with the FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function apiClient(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const defaultHeaders = {
    'Accept': 'application/json',
  };

  if (options.body && !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData?.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : errorData.detail.message || JSON.stringify(errorData.detail);
        } else if (errorData?.error?.message) {
          errorMessage = errorData.error.message;
        }
      } catch {
        // Use default fallback error message
      }
      const error = new Error(errorMessage);
      error.status = response.status;
      throw error;
    }

    return await response.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Unable to connect to the backend server. Please check your network connection.');
    }
    throw err;
  }
}
