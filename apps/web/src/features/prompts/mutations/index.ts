/**
 * @file index.ts
 * @description Prompts Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useSavePromptMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (promptData: Record<string, unknown>) => {
      // TODO: Save prompt via API POST /api/prompts
      return promptData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
    },
  });
}
