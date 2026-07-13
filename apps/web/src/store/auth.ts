import { create } from 'zustand';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: { email: string; full_name: string; id: string } | null;
  activeOrgId: string | null;
  setAuth: (token: string, refreshToken: string, user: { email: string; full_name: string; id: string }) => void;
  setActiveOrgId: (orgId: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof window !== 'undefined' ? localStorage.getItem('token') : null,
  refreshToken: typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null,
  user: typeof window !== 'undefined' ? JSON.parse(localStorage.getItem('user') || 'null') : null,
  activeOrgId: typeof window !== 'undefined' ? localStorage.getItem('active_org_id') : null,
  
  setAuth: (token, refreshToken, user) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
      localStorage.setItem('refresh_token', refreshToken);
      localStorage.setItem('user', JSON.stringify(user));
    }
    set({ token, refreshToken, user });
  },
  
  setActiveOrgId: (orgId) => {
    if (typeof window !== 'undefined') {
      if (orgId) {
        localStorage.setItem('active_org_id', orgId);
      } else {
        localStorage.removeItem('active_org_id');
      }
    }
    set({ activeOrgId: orgId });
  },
  
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      localStorage.removeItem('active_org_id');
    }
    set({ token: null, refreshToken: null, user: null, activeOrgId: null });
  },
}));
