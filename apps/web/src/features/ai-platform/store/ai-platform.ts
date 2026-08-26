import { create } from 'zustand';

// LocalStorage persistence helpers with SSR safety
const FAVORITES_STORAGE_KEY = 'ai_platform_favorites';

const getPersistedFavorites = (): string[] => {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(FAVORITES_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.warn('Failed to load favorites from localStorage:', err);
    return [];
  }
};

const persistFavorites = (favorites: string[]) => {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(favorites));
  } catch (err) {
    console.warn('Failed to save favorites to localStorage:', err);
  }
};

interface AIPlatformState {
  // Provider / Model filters
  selectedProvider: string | null;
  setSelectedProvider: (provider: string | null) => void;
  selectedModel: string | null;
  setSelectedModel: (model: string | null) => void;
  
  // Search and view preferences
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  viewPreference: 'grid' | 'table';
  setViewPreference: (pref: 'grid' | 'table') => void;
  
  // Time range
  timeRange: '24h' | '7d' | '30d' | '90d';
  setTimeRange: (range: '24h' | '7d' | '30d' | '90d') => void;
  
  // Model favorites
  favorites: string[];
  toggleFavorite: (modelId: string) => void;
  initializeFavorites: () => void;
  setFavorites: (favorites: string[]) => void;
  
  // Model comparison list
  comparisonModels: string[];
  addToComparison: (modelId: string) => void;
  removeFromComparison: (modelId: string) => void;
  clearComparison: () => void;
}

export const useAIPlatformStore = create<AIPlatformState>((set) => ({
  selectedProvider: null,
  setSelectedProvider: (selectedProvider) => set({ selectedProvider }),
  selectedModel: null,
  setSelectedModel: (selectedModel) => set({ selectedModel }),
  
  searchQuery: '',
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  viewPreference: 'grid',
  setViewPreference: (viewPreference) => set({ viewPreference }),
  
  timeRange: '7d',
  setTimeRange: (timeRange) => set({ timeRange }),
  
  favorites: getPersistedFavorites(),
  initializeFavorites: () => {
    const loaded = getPersistedFavorites();
    set({ favorites: loaded });
  },
  setFavorites: (favorites) => {
    persistFavorites(favorites);
    set({ favorites });
  },
  toggleFavorite: (modelId) => set((state) => {
    const nextFavorites = state.favorites.includes(modelId)
      ? state.favorites.filter((id) => id !== modelId)
      : [...state.favorites, modelId];
    persistFavorites(nextFavorites);
    return { favorites: nextFavorites };
  }),
  
  comparisonModels: [],
  addToComparison: (modelId) => set((state) => ({
    comparisonModels: state.comparisonModels.includes(modelId)
      ? state.comparisonModels
      : state.comparisonModels.length >= 3
        ? [...state.comparisonModels.slice(1), modelId]
        : [...state.comparisonModels, modelId]
  })),
  removeFromComparison: (modelId) => set((state) => ({
    comparisonModels: state.comparisonModels.filter((id) => id !== modelId)
  })),
  clearComparison: () => set({ comparisonModels: [] })
}));
