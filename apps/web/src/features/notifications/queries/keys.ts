/**
 * Notifications Query Key Factory.
 */

export const notificationKeys = {
  all: ['notifications'] as const,
  list: () => [...notificationKeys.all, 'list'] as const,
  preferences: () => [...notificationKeys.all, 'preferences'] as const,
};
