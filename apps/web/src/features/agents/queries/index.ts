/**
 * @file index.ts
 * @description Agents TanStack React Query Hooks.
 */

import { useQuery } from '@tanstack/react-query';
import { fetchAgents } from '../services';

export function useAgentsQuery() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => fetchAgents(),
  });
}
