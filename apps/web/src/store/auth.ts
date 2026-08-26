import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// P2-11: lightweight session marker cookie consumed by src/middleware.ts route guard.
const SESSION_COOKIE = 'eaimos.session';

function setSessionCookie() {
  if (typeof document === 'undefined') return;
  document.cookie = `${SESSION_COOKIE}=1; path=/; SameSite=Lax; max-age=2592000`;
}

function clearSessionCookie() {
  if (typeof document === 'undefined') return;
  document.cookie = `${SESSION_COOKIE}=; path=/; SameSite=Lax; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role?: string | null;
  permissions?: string[];
  deletion_requested_at?: string | null;
  metadata_json?: Record<string, any> | null;
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
      
      setAuth: (accessToken, refreshToken, user) => {
        set({ accessToken, refreshToken, user });
        setSessionCookie();
      },
      setOrganizations: (organizations) => set({ organizations }),
      setActiveOrg: (activeOrg) => set({ activeOrg }),

      logout: () => {
        clearSessionCookie();
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          activeOrg: null,
          organizations: [],
        });
      },
    }),
    {
      name: 'eaimos-auth-storage',
    }
  )
);
