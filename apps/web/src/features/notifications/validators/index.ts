/**
 * @file index.ts
 * @description Validators for Notifications.
 */

export function validateNotificationPayload(title: string, message: string): boolean {
  return title.trim().length > 0 && message.trim().length > 0;
}
