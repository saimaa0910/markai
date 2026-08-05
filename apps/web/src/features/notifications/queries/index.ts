/**
 * Notifications React Query Hooks.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationKeys } from './keys';
import { notificationsApi } from '../services/api';
import type { SendNotificationPayload } from '../types';

export function useNotificationsList() {
  return useQuery({
    queryKey: notificationKeys.list(),
    queryFn: notificationsApi.list,
  });
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: notificationKeys.preferences(),
    queryFn: notificationsApi.getPreferences,
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: notificationKeys.all }); },
  });
}

export function useMarkAllNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => { qc.invalidateQueries({ queryKey: notificationKeys.all }); },
  });
}

export function useSendNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SendNotificationPayload) => notificationsApi.send(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: notificationKeys.all }); },
  });
}
