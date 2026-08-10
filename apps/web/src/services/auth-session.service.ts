import { apiClient } from './api-client';

export interface Session {
  id: string;
  user_id: string;
  device_name?: string;
  device_type?: string;
  device_os?: string;
  browser?: string;
  ip_address?: string;
  location?: string;
  is_current: boolean;
  last_active_at: string;
  created_at: string;
  expires_at: string;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
  active_count: number;
}

/**
 * Session Management API Service
 * Handles session listing, revocation, and management for Sprint 8.3.1
 */
export const authSessionService = {
  /**
   * Get all active sessions for the current user
   */
  async listSessions(): Promise<SessionListResponse> {
    const response = await apiClient.get<SessionListResponse>('/auth/sessions');
    return response.data;
  },

  /**
   * Revoke a specific session by ID
   * @param sessionId - The session ID to revoke
   */
  async revokeSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/auth/sessions/${sessionId}`);
  },

  /**
   * Revoke all sessions except the current one
   */
  async revokeAllOtherSessions(): Promise<void> {
    await apiClient.delete('/auth/sessions', {
      params: { exclude_current: true }
    });
  },

  /**
   * Revoke all sessions including the current one (full logout)
   */
  async revokeAllSessions(): Promise<void> {
    await apiClient.delete('/auth/sessions');
  },
};
