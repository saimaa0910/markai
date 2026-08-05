/**
 * @file index.ts
 * @description SEO Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useAddKeywordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (keywordTerm: string) => {
      // TODO: Call API endpoint POST /api/seo/keywords
      return { term: keywordTerm };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seo-keywords'] });
    },
  });
}
