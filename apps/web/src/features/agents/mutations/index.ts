/**
 * @file index.ts
 * @description Agents Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useCreateAgentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newAgent: Record<string, unknown>) => {
      // TODO: Call API endpoint POST /api/agents
      return newAgent;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
