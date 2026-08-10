import { apiClient } from './api-client';

export interface AccountDeactivateRequest {
  reason?: string;
  feedback?: string;
}

export interface AccountDeletionRequest {
  password: string;
  reason?: string;
  confirmation_text: string;
}

export interface DataExportRequest {
  format: 'json' | 'csv';
  include_files?: boolean;
}

export interface DataExportStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  format: string;
  download_url?: string;
  created_at: string;
  expires_at?: string;
}

export interface PrivacyDashboard {
  account_status: string;
  deletion_scheduled: boolean;
  deletion_scheduled_for?: string;
  data_retention_days: number;
  can_cancel_deletion: boolean;
  active_sessions_count: number;
  trusted_devices_count: number;
  recent_exports: DataExportStatus[];
}

/**
 * Account Lifecycle API Service
 * Handles account deactivation, deletion, reactivation, and data export
 */
export const accountLifecycleService = {
  /**
   * Deactivate the current user account
   */
  async deactivateAccount(data: AccountDeactivateRequest): Promise<void> {
    await apiClient.post('/account/deactivate', data);
  },

  /**
   * Reactivate a previously deactivated account
   */
  async reactivateAccount(): Promise<void> {
    await apiClient.post('/account/reactivate');
  },

  /**
   * Request account deletion with 7-day grace period
   */
  async requestAccountDeletion(data: AccountDeletionRequest): Promise<void> {
    await apiClient.post('/account/deletion/request', data);
  },

  /**
   * Cancel a pending account deletion
   */
  async cancelAccountDeletion(): Promise<void> {
    await apiClient.delete('/account/deletion/cancel');
  },

  /**
   * Immediately delete account (admin only)
   */
  async deleteAccountImmediately(password: string): Promise<void> {
    await apiClient.delete('/account/deletion/immediate', {
      data: { password }
    });
  },

  /**
   * Request a data export (GDPR compliance)
   */
  async requestDataExport(data: DataExportRequest): Promise<DataExportStatus> {
    const response = await apiClient.post<DataExportStatus>('/account/export', data);
    return response.data;
  },

  /**
   * Get status of a data export
   */
  async getDataExportStatus(exportId: string): Promise<DataExportStatus> {
    const response = await apiClient.get<DataExportStatus>(`/account/export/${exportId}`);
    return response.data;
  },

  /**
   * Get privacy dashboard with account status and data
   */
  async getPrivacyDashboard(): Promise<PrivacyDashboard> {
    const response = await apiClient.get<PrivacyDashboard>('/account/privacy-dashboard');
    return response.data;
  },
};
