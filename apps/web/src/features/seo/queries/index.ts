/**
 * SEO React Query Hooks.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { seoKeys } from './keys';
import { seoApi } from '../services/api';

export function useSEOOverview() {
  return useQuery({
    queryKey: seoKeys.overview(),
    queryFn: seoApi.getOverview,
  });
}

export function useAddKeyword() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (keyword: string) => seoApi.addKeyword(keyword),
    onSuccess: () => { qc.invalidateQueries({ queryKey: seoKeys.all }); },
  });
}

export function useRunAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (domain: string) => seoApi.runAudit(domain),
    onSuccess: () => { qc.invalidateQueries({ queryKey: seoKeys.all }); },
  });
}
