/**
 * @file index.ts
 * @description Notifications Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useMarkAsReadMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (notificationId: string) => {
      // TODO: Execute PUT /api/notifications/{id}/read
      return { id: notificationId, read: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}
