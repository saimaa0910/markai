/**
 * Campaign API Service — Connects to existing backend endpoints.
 * @see apps/api/src/api/routes/campaigns.py
 */

import { apiClient } from '@/services/api-client';
import type { Campaign, CampaignCreate, CampaignUpdate, CampaignTrackRequest } from '../types';

export const campaignsApi = {
  list: () => apiClient.get<Campaign[]>('/campaigns').then(r => r.data),
  get: (id: string) => apiClient.get<Campaign>(`/campaigns/${id}`).then(r => r.data),
  create: (data: CampaignCreate) => apiClient.post<Campaign>('/campaigns', data).then(r => r.data),
  update: (id: string, data: CampaignUpdate) => apiClient.put<Campaign>(`/campaigns/${id}`, data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/campaigns/${id}`),
  execute: (id: string) => apiClient.post<Campaign>(`/campaigns/${id}/execute`).then(r => r.data),
  track: (id: string, data: CampaignTrackRequest) => apiClient.post<Campaign>(`/campaigns/${id}/track`, data).then(r => r.data),
};
