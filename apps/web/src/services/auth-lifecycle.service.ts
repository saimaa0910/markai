import { apiClient } from './api-client';

/**
 * Auth Lifecycle API Service for Sprint 8.3.1
 * Handles password reset and email verification flows
 */
export const authLifecycleService = {
  /**
   * Step 1: Request password reset email
   */
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post('/auth/password-reset/request', { email });
  },

  /**
   * Step 2: Verify password reset token
   */
  async verifyPasswordResetToken(token: string): Promise<{ valid: boolean; email?: string }> {
    const response = await apiClient.post<{ valid: boolean; email?: string }>(
      '/auth/password-reset/verify',
      { token }
    );
    return response.data;
  },

  /**
   * Step 3: Complete password reset with new password
   */
  async completePasswordReset(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/password-reset/complete', {
      token,
      new_password: newPassword
    });
  },

  /**
   * Verify email with token
   */
  async verifyEmail(token: string): Promise<void> {
    await apiClient.post('/auth/verify-email', { token });
  },

  /**
   * Resend email verification
   */
  async resendVerification(email: string): Promise<void> {
    await apiClient.post('/auth/resend-verification', { email });
  },
};
