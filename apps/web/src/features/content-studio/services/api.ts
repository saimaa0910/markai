/**
 * Content Studio API Service Client.
 */
import { apiClient } from '@/services/api-client';
import type { ContentResponse, ContentGenerateRequest } from '../types';

export const contentStudioApi = {
  list: () => apiClient.get<ContentResponse[]>('/agents/content/history').then(r => r.data),
  generate: (data: ContentGenerateRequest) => apiClient.post<ContentResponse>('/agents/content/generate', data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/agents/content/history/${id}`),
};
