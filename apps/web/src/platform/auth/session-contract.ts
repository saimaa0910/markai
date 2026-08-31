/**
 * @file session-contract.ts
 * @description Zero-Token BFF PublicSession Interface & Session Attributes.
 * 
 * Enterprise Security Rule:
 * Tokens (Access & Refresh JWTs) must never reach browser storage or client state.
 * The browser only interacts with the sanitized `PublicSession` profile.
 */

export interface PublicSession {
  isAuthenticated: boolean;
  userId: string;
  email: string;
  fullName: string;
  tenantId?: string | null;
  roles: string[];
  permissions: string[];
  expiresAt: number; // Unix timestamp in seconds
  actorType: 'user' | 'service' | 'agent';
}

export const SESSION_COOKIE_NAME = 'eaimos.session';

export interface CookieSecurityOptions {
  name: string;
  value: string;
  httpOnly?: boolean;
  secure?: boolean;
  sameSite?: 'lax' | 'strict' | 'none';
  path?: string;
  maxAge?: number;
}
