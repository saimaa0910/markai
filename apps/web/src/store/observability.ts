import { create } from 'zustand';

interface ObservabilityState {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  levelFilter: string;
  setLevelFilter: (level: string) => void;
  selectedTraceId: string | null;
  setSelectedTraceId: (id: string | null) => void;
  selectedTimeframeDays: number;
  setSelectedTimeframeDays: (days: number) => void;
}

export const useObservabilityStore = create<ObservabilityState>((set) => ({
  activeTab: 'overview',
  setActiveTab: (activeTab) => set({ activeTab }),
  searchQuery: '',
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  levelFilter: 'ALL',
  setLevelFilter: (levelFilter) => set({ levelFilter }),
  selectedTraceId: null,
  setSelectedTraceId: (selectedTraceId) => set({ selectedTraceId }),
  selectedTimeframeDays: 7,
  setSelectedTimeframeDays: (selectedTimeframeDays) => set({ selectedTimeframeDays }),
}));
