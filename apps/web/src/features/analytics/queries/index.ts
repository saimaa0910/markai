/**
 * Analytics React Query Hooks.
 */

import { useQuery } from '@tanstack/react-query';
import { analyticsKeys } from './keys';
import { analyticsApi } from '../services/api';

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: analyticsKeys.overview(),
    queryFn: analyticsApi.getOverview,
  });
}
