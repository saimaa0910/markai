/**
 * @file user-message.ts
 * @description Centralized Error Code Leak-Stop and Safe User Message Resolution.
 * 
 * Enterprise Security Rule:
 * Frontend code must never render raw backend error.message or SQL exception strings directly.
 * All API errors must pass through this centralized resolver to prevent information disclosure.
 */

export interface MachineErrorEnvelope {
  code: string;
  message?: string;
  detail?: string;
  request_id?: string;
  fields?: Array<{ field: string; code: string; message: string }>;
}

export interface ApiErrorResponse {
  success?: boolean;
  error?: MachineErrorEnvelope;
  detail?: string | MachineErrorEnvelope;
}

const SAFE_MESSAGES: Record<string, string> = {
  // Authentication & Session
  unauthenticated: 'Your session has expired. Please sign in again.',
  unauthorized: 'Your session has expired. Please sign in again.',
  invalid_credentials: 'The email or password you entered is incorrect.',
  session_expired: 'Your session has timed out. Please log in again.',
  account_deactivated: 'This account has been temporarily deactivated. Please contact support.',
  account_locked: 'This account is temporarily locked due to excessive failed attempts. Please try again later.',
  email_unverified: 'Please verify your email address to proceed.',
  mfa_required: 'Multi-factor authentication is required to access this resource.',
  forbidden: 'You do not have sufficient permissions to perform this action.',
  
  // Resource & State
  resource_not_found: 'The requested resource could not be found.',
  not_found: 'The requested resource could not be found.',
  conflict: 'A conflict occurred with existing resource state.',
  duplicate_resource: 'An item with this name or identifier already exists.',
  
  // Validation & Inputs
  validation_failed: 'Please check your inputs and correct the highlighted fields.',
  invalid_input: 'The provided data is invalid. Please check and try again.',
  bad_request: 'The request could not be processed. Please check your inputs.',
  
  // Rate Limiting & Throttling
  rate_limited: 'You have reached the request limit. Please wait a moment and try again.',
  too_many_requests: 'Too many requests. Please slow down and try again shortly.',
  quota_exceeded: 'Organization credit quota has been reached. Please contact your administrator.',
  
  // Platform & Server
  internal_error: 'An unexpected system error occurred. Please try again shortly.',
  internal_server_error: 'An unexpected system error occurred. Please try again shortly.',
  service_unavailable: 'The service is temporarily unavailable. Our team has been notified.',
  network_error: 'Unable to reach the Viptant server. Please check your internet connection.',
  timeout_error: 'The request timed out. Please try again in a few moments.',
};

/**
 * Extracts a normalized machine error code from an unknown error object.
 */
export function extractErrorCode(error: unknown): string | null {
  if (!error || typeof error !== 'object') return null;

  const err = error as Record<string, any>;

  // 1. Check Axios response data envelope: error.response.data.error.code
  if (err.response?.data?.error?.code) {
    return String(err.response.data.error.code).toLowerCase();
  }

  // 2. Check FastAPI error.response.data.detail (if machine code string)
  if (typeof err.response?.data?.detail === 'string') {
    const detail = err.response.data.detail.trim().toLowerCase();
    // Only treat as code if it resembles an identifier without spaces
    if (/^[a-z0-9_-]+$/.test(detail) && SAFE_MESSAGES[detail]) {
      return detail;
    }
  }

  // 3. Check error code on error object directly
  if (err.code && typeof err.code === 'string') {
    const code = err.code.toLowerCase();
    if (code === 'econnaborted' || code === 'err_network') {
      return 'network_error';
    }
    if (SAFE_MESSAGES[code]) {
      return code;
    }
  }

  // 4. Derive from HTTP status code
  const status = err.response?.status;
  if (status === 401) return 'unauthorized';
  if (status === 403) return 'forbidden';
  if (status === 404) return 'resource_not_found';
  if (status === 409) return 'conflict';
  if (status === 422) return 'validation_failed';
  if (status === 429) return 'rate_limited';
  if (status === 500 || status === 502 || status === 503 || status === 504) return 'internal_server_error';

  return null;
}

/**
 * Returns a safe, user-facing error message without leaking sensitive backend details.
 */
export function getSafeErrorMessage(error: unknown, fallback?: string): string {
  const code = extractErrorCode(error);
  if (code && SAFE_MESSAGES[code]) {
    return SAFE_MESSAGES[code];
  }

  // Check if error is an Axios network timeout
  const err = error as Record<string, any>;
  if (err?.code === 'ECONNABORTED' || (typeof err?.message === 'string' && err.message.includes('timeout'))) {
    return SAFE_MESSAGES.timeout_error;
  }
  if (err?.message === 'Network Error' || !err?.response) {
    if (err?.message && !err.response && typeof window !== 'undefined' && !navigator.onLine) {
      return 'You appear to be offline. Please check your internet connection.';
    }
  }

  return fallback || SAFE_MESSAGES.internal_error;
}
