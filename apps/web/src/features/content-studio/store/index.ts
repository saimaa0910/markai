/**
 * @file index.ts
 * @description Zustand state store for Content Studio.
 */

import { create } from 'zustand';

export interface ContentStudioState {
  activeContentId: string | null;
  setActiveContentId: (id: string | null) => void;
}

export const useContentStudioStore = create<ContentStudioState>((set) => ({
  activeContentId: null,
  setActiveContentId: (id) => set({ activeContentId: id }),
}));
