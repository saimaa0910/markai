import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserProfile | null;
  activeOrg: Organization | null;
  organizations: Organization[];
  setAuth: (accessToken: string, refreshToken: string, user: UserProfile) => void;
  setOrganizations: (orgs: Organization[]) => void;
  setActiveOrg: (org: Organization | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      activeOrg: null,
      organizations: [],
      
      setAuth: (accessToken, refreshToken, user) => set({ accessToken, refreshToken, user }),
      setOrganizations: (organizations) => set({ organizations }),
      setActiveOrg: (activeOrg) => set({ activeOrg }),
      
      logout: () => set({ 
        accessToken: null, 
        refreshToken: null, 
        user: null, 
        activeOrg: null, 
        organizations: [] 
      }),
    }),
    {
      name: 'eaimos-auth-storage',
    }
  )
);
