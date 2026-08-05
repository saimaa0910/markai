/**
 * Campaign React Query Hooks.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { campaignKeys } from './keys';
import { campaignsApi } from '../services/api';
import type { CampaignCreate, CampaignUpdate, CampaignTrackRequest } from '../types';

export function useCampaigns() {
  return useQuery({
    queryKey: campaignKeys.list(),
    queryFn: campaignsApi.list,
  });
}

export function useCampaign(id: string) {
  return useQuery({
    queryKey: campaignKeys.detail(id),
    queryFn: () => campaignsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CampaignCreate) => campaignsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: campaignKeys.all }); },
  });
}

export function useUpdateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CampaignUpdate }) => campaignsApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: campaignKeys.all }); },
  });
}

export function useDeleteCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => campaignsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: campaignKeys.all }); },
  });
}

export function useExecuteCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => campaignsApi.execute(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: campaignKeys.all }); },
  });
}

export function useTrackCampaignEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CampaignTrackRequest }) => campaignsApi.track(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: campaignKeys.all }); },
  });
}
