/**
 * @file slice.ts
 * @description Zustand state store slice for Organizations feature.
 */

import { create } from 'zustand';

export interface OrganizationState {
  activeOrgId: string | null;
  setActiveOrgId: (id: string | null) => void;
}

export const useOrganizationStore = create<OrganizationState>((set) => ({
  activeOrgId: null,
  setActiveOrgId: (id) => set({ activeOrgId: id }),
}));
