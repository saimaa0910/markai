/**
 * @file index.ts
 * @description Zustand state store for CRM feature.
 */

import { create } from 'zustand';

export interface CRMState {
  activeContactId: string | null;
  setActiveContactId: (id: string | null) => void;
}

export const useCRMStore = create<CRMState>((set) => ({
  activeContactId: null,
  setActiveContactId: (id) => set({ activeContactId: id }),
}));
