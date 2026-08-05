/**
 * @file index.ts
 * @description Content Studio Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useCreateContentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (contentData: Record<string, unknown>) => {
      // TODO: Execute POST /api/content-studio/create
      return contentData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-items'] });
    },
  });
}
