/**
 * @file index.ts
 * @description Zustand state store for SEO feature.
 */

import { create } from 'zustand';

export interface SEOState {
  selectedKeywordId: string | null;
  setSelectedKeywordId: (id: string | null) => void;
}

export const useSEOStore = create<SEOState>((set) => ({
  selectedKeywordId: null,
  setSelectedKeywordId: (id) => set({ selectedKeywordId: id }),
}));
