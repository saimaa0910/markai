/**
 * @file index.ts
 * @description Zustand state store for Agents feature.
 */

import { create } from 'zustand';

export interface AgentState {
  selectedAgentId: string | null;
  setSelectedAgentId: (id: string | null) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  selectedAgentId: null,
  setSelectedAgentId: (id) => set({ selectedAgentId: id }),
}));
