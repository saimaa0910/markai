/**
 * @file slice.ts
 * @description CRM Zustand State Slice.
 */

import { create } from 'zustand';

export interface CRMSliceState {
  activeId: string | null;
  setActiveId: (id: string | null) => void;
}

export const useCRMSliceStore = create<CRMSliceState>((set) => ({
  activeId: null,
  setActiveId: (id) => set({ activeId: id }),
}));
