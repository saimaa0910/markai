/**
 * Content Studio React Query Hooks.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contentKeys } from './keys';
import { contentStudioApi } from '../services/api';
import type { ContentGenerateRequest } from '../types';

export function useContentList() {
  return useQuery({
    queryKey: contentKeys.list(),
    queryFn: contentStudioApi.list,
  });
}

export function useGenerateContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ContentGenerateRequest) => contentStudioApi.generate(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: contentKeys.all }); },
  });
}

export function useDeleteContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => contentStudioApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: contentKeys.all }); },
  });
}
