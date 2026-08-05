/**
 * @file index.ts
 * @description Prompts TanStack Query Hooks.
 */

import { useQuery } from '@tanstack/react-query';

export function usePromptsQuery() {
  return useQuery({
    queryKey: ['prompts'],
    queryFn: async () => {
      // TODO: Fetch prompt templates from API
      return [];
    },
  });
}
