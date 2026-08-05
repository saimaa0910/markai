/**
 * @file index.ts
 * @description Knowledge Base Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useUploadDocumentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (fileData: FormData) => {
      // TODO: Call API endpoint POST /api/knowledge/upload
      return { success: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
  });
}
