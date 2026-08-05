/**
 * @file index.ts
 * @description Workflows Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useExecuteWorkflowMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (workflowId: string) => {
      // TODO: Post workflow execution to API /api/workflows/{id}/execute
      return { status: 'queued', workflowId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}
