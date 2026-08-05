/**
 * @file create.ts
 * @description Create Contact Mutation.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { crmKeys } from '../queries/keys';

export function useCreateContactApiMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => payload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.contacts() });
    },
  });
}
