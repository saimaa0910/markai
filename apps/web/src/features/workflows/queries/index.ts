/**
 * @file index.ts
 * @description Workflows Query Hooks.
 */

import { useQuery } from '@tanstack/react-query';
import { fetchWorkflows } from '../services';

export function useWorkflowsQuery() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () => fetchWorkflows(),
  });
}
