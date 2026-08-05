/**
 * @file create.ts
 * @description Organization Creation Mutation Hook.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationKeys } from '../queries/keys';

export function useCreateOrganizationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orgData: { name: string; slug: string }) => {
      // TODO: Execute POST /api/organizations
      return orgData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: organizationKeys.all });
    },
  });
}
