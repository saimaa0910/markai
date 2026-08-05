/**
 * @file index.ts
 * @description AI Platform Query Hooks.
 */

import { useQuery } from '@tanstack/react-query';
import { fetchAIProviders } from '../services';

export function useAIProvidersQuery() {
  return useQuery({
    queryKey: ['ai-providers'],
    queryFn: () => fetchAIProviders(),
  });
}
