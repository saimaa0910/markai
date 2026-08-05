/**
 * @file index.ts
 * @description CRM Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useCreateContactMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (contactData: Record<string, unknown>) => {
      // TODO: Execute POST /api/crm/contacts
      return contactData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-contacts'] });
    },
  });
}
