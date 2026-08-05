/**
 * Notifications API Service Client.
 */

import { apiClient } from '@/services/api-client';
import type { NotificationItem, SendNotificationPayload, NotificationPreference } from '../types';

export const notificationsApi = {
  list: () => apiClient.get<NotificationItem[]>('/notifications/').then(r => r.data),
  markRead: (id: string) => apiClient.patch<NotificationItem>(`/notifications/${id}/read`).then(r => r.data),
  markAllRead: () => apiClient.post('/notifications/read-all').then(r => r.data),
  send: (data: SendNotificationPayload) => apiClient.post<NotificationItem>('/notifications/send', data).then(r => r.data),
  getPreferences: () => apiClient.get<NotificationPreference[]>('/notifications/preferences').then(r => r.data),
};
