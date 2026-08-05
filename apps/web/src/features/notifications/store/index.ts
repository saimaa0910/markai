/**
 * @file index.ts
 * @description Zustand state store for Notifications feature.
 */

import { create } from 'zustand';

export interface NotificationState {
  unreadCount: number;
  setUnreadCount: (count: number) => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  unreadCount: 0,
  setUnreadCount: (count) => set({ unreadCount: count }),
}));
