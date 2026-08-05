/**
 * Notifications Platform Feature Types.
 * @see apps/api/src/api/routes/notifications.py
 */

export type NotificationChannel = 'EMAIL' | 'SMS' | 'PUSH' | 'IN_APP';
export type NotificationPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  is_read: boolean;
  action_url?: string | null;
  created_at: string;
}

export interface SendNotificationPayload {
  recipient_id: string;
  title: string;
  message: string;
  channel: NotificationChannel;
  priority?: NotificationPriority;
  action_url?: string;
}

export interface NotificationPreference {
  id: string;
  channel: NotificationChannel;
  enabled: boolean;
}
