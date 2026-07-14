import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PromptsState {
  selectedPromptId: string | null;
  selectedPromptName: string | null;
  activeEditorContent: string;
  testVariables: Record<string, string>;
  testProvider: string;
  testModel: string;
  favorites: string[];
  filters: {
    category: string;
    tag: string;
    search: string;
  };

  setSelectedPromptId: (id: string | null, name: string | null) => void;
  setActiveEditorContent: (content: string) => void;
  setTestVariable: (key: string, value: string) => void;
  clearTestVariables: () => void;
  setTestProvider: (provider: string) => void;
  setTestModel: (model: string) => void;
  toggleFavorite: (name: string) => void;
  setFilters: (filters: Partial<PromptsState['filters']>) => void;
}

export const usePromptsStore = create<PromptsState>()(
  persist(
    (set) => ({
      selectedPromptId: null,
      selectedPromptName: null,
      activeEditorContent: '',
      testVariables: {},
      testProvider: 'openai',
      testModel: 'gpt-4o',
      favorites: [],
      filters: {
        category: 'all',
        tag: '',
        search: '',
      },

      setSelectedPromptId: (id, name) => set({ selectedPromptId: id, selectedPromptName: name }),
      setActiveEditorContent: (content) => set({ activeEditorContent: content }),
      setTestVariable: (key, value) =>
        set((state) => ({ testVariables: { ...state.testVariables, [key]: value } })),
      clearTestVariables: () => set({ testVariables: {} }),
      setTestProvider: (provider) => set({ testProvider: provider }),
      setTestModel: (model) => set({ testModel: model }),
      toggleFavorite: (name) =>
        set((state) => {
          const isFav = state.favorites.includes(name);
          return {
            favorites: isFav
              ? state.favorites.filter((x) => x !== name)
              : [...state.favorites, name],
          };
        }),
      setFilters: (filters) =>
        set((state) => ({ filters: { ...state.filters, ...filters } })),
    }),
    {
      name: 'viptant-prompts-store',
      partialize: (state) => ({
        favorites: state.favorites,
        testProvider: state.testProvider,
        testModel: state.testModel,
      }),
    }
  )
);
