import { apiClient } from './api-client';

export interface TrustedDevice {
  id: string;
  device_name: string;
  device_type: string;
  device_os?: string;
  browser?: string;
  last_used_at: string;
  trusted_at: string;
  is_current: boolean;
}

export interface TrustDeviceRequest {
  device_fingerprint: string;
  device_name?: string;
  remember_for_days?: number;
}

export interface MFARecoveryCode {
  code: string;
  used: boolean;
  used_at?: string;
}

export interface MFARecoveryCodesResponse {
  codes: string[];
  generated_at: string;
  expires_at: string;
}

export interface AuditLog {
  id: string;
  event_type: string;
  event_category: string;
  description: string;
  ip_address?: string;
  user_agent?: string;
  location?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface AuditLogsResponse {
  logs: AuditLog[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Security API Service
 * Handles device trust, MFA recovery, and audit logs
 */
export const securityService = {
  // ===== Device Trust =====
  
  /**
   * Get all trusted devices for the current user
   */
  async listTrustedDevices(): Promise<TrustedDevice[]> {
    const response = await apiClient.get<{ devices: TrustedDevice[] }>('/security/devices');
    return response.data.devices;
  },

  /**
   * Trust the current device
   */
  async trustDevice(data: TrustDeviceRequest): Promise<void> {
    await apiClient.post('/security/devices/trust', data);
  },

  /**
   * Remove trust from a device
   */
  async removeTrustedDevice(deviceId: string): Promise<void> {
    await apiClient.delete(`/security/devices/${deviceId}`);
  },

  // ===== MFA Recovery =====
  
  /**
   * Generate new MFA recovery codes
   */
  async generateRecoveryCodes(): Promise<MFARecoveryCodesResponse> {
    const response = await apiClient.post<MFARecoveryCodesResponse>('/security/mfa/recovery-codes/generate');
    return response.data;
  },

  /**
   * Get existing recovery codes (shows which are used)
   */
  async getRecoveryCodes(): Promise<MFARecoveryCode[]> {
    const response = await apiClient.get<{ codes: MFARecoveryCode[] }>('/security/mfa/recovery-codes');
    return response.data.codes;
  },

  /**
   * Verify and use an MFA recovery code
   */
  async verifyRecoveryCode(code: string): Promise<{ valid: boolean; access_token?: string }> {
    const response = await apiClient.post<{ valid: boolean; access_token?: string }>(
      '/security/mfa/recovery-codes/verify',
      { recovery_code: code }
    );
    return response.data;
  },

  // ===== Audit Logs =====
  
  /**
   * Get audit logs for the current user
   */
  async getAuditLogs(params?: {
    event_type?: string;
    page?: number;
    page_size?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<AuditLogsResponse> {
    const response = await apiClient.get<AuditLogsResponse>('/audit/logs', { params });
    return response.data;
  },

  /**
   * Get security events summary
   */
  async getSecurityEventsSummary(): Promise<{
    total_events: number;
    recent_logins: number;
    failed_attempts: number;
    device_changes: number;
  }> {
    const response = await apiClient.get('/audit/security-summary');
    return response.data;
  },
};
