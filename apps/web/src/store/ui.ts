import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
  
  notificationsOpen: boolean;
  setNotificationsOpen: (open: boolean) => void;
  
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  
  commandPaletteOpen: false,
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  
  notificationsOpen: false,
  setNotificationsOpen: (open) => set({ notificationsOpen: open }),
  
  globalLoading: false,
  setGlobalLoading: (loading) => set({ globalLoading: loading }),
}));
