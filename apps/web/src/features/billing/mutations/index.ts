/**
 * @file index.ts
 * @description Billing Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useSubscribeToPlanMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planId: string) => {
      // TODO: Execute POST /api/billing/subscribe
      return { planId, status: 'success' };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-subscription'] });
    },
  });
}
