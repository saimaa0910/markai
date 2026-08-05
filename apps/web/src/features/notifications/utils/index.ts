/**
 * @file index.ts
 * @description Utility functions for Notifications.
 */

export function countUnreadNotifications(items: { read: boolean }[]): number {
  return items.filter((item) => !item.read).length;
}
