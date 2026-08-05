/**
 * @file index.ts
 * @description Zustand state store for Campaigns feature.
 */

import { create } from 'zustand';

export interface CampaignState {
  selectedCampaignId: string | null;
  setSelectedCampaignId: (id: string | null) => void;
}

export const useCampaignStore = create<CampaignState>((set) => ({
  selectedCampaignId: null,
  setSelectedCampaignId: (id) => set({ selectedCampaignId: id }),
}));
