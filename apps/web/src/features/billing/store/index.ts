/**
 * @file index.ts
 * @description Zustand state store for Billing feature.
 */

import { create } from 'zustand';

export interface BillingState {
  selectedPlanId: string | null;
  setSelectedPlanId: (id: string | null) => void;
}

export const useBillingStore = create<BillingState>((set) => ({
  selectedPlanId: null,
  setSelectedPlanId: (id) => set({ selectedPlanId: id }),
}));
