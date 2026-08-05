/**
 * @file index.ts
 * @description Zustand state store for Workflows editor.
 */

import { create } from 'zustand';

export interface WorkflowState {
  activeWorkflowId: string | null;
  setActiveWorkflowId: (id: string | null) => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  activeWorkflowId: null,
  setActiveWorkflowId: (id) => set({ activeWorkflowId: id }),
}));
