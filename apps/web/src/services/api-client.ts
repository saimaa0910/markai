import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL 
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : (typeof window !== 'undefined' 
      ? (window.location.port === '3000' ? 'http://localhost:8000/api/v1' : '/api/v1')
      : 'http://localhost:8000/api/v1');

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach access token & active tenant organization ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const authStorage = localStorage.getItem('eaimos-auth-storage');
      if (authStorage) {
        try {
          const parsed = JSON.parse(authStorage);
          const token = parsed.state?.accessToken;
          if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
          }
          const orgId = parsed.state?.activeOrg?.id;
          if (orgId && config.headers) {
            config.headers['X-Organization-ID'] = orgId;
          }
        } catch (e) {
          console.error('Failed to parse auth token/org from storage', e);
        }
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle errors and refresh triggers
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    
    // Auto-refresh token if 401 Unauthorized
    if (error.response?.status === 401 && originalRequest && !(originalRequest as any)._retry) {
      (originalRequest as any)._retry = true;
      try {
        const authStorage = localStorage.getItem('eaimos-auth-storage');
        if (authStorage) {
          const parsed = JSON.parse(authStorage);
          const refreshToken = parsed.state?.refreshToken;
          
          if (refreshToken) {
            const refreshRes = await axios.post(`${API_BASE_URL}/auth/refresh?refresh_token=${refreshToken}`);
            const { access_token, refresh_token } = refreshRes.data;
            
            // Save back to Zustand store directly!
            useAuthStore.setState({ accessToken: access_token, refreshToken: refresh_token });
            
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }
            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        console.error('Session refresh failed. Redirecting to logout...', refreshError);
        if (typeof window !== 'undefined') {
          localStorage.removeItem('eaimos-auth-storage');
          window.location.href = '/auth/login?expired=true';
        }
      }
    }

    // Enhance timeout/network errors with descriptive message fields
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      error.message = 'The server request timed out. Please verify provider connectivity and try again.';
    } else if (!error.response) {
      error.message = 'Network error: Cannot reach the Viptant API server.';
    }

    return Promise.reject(error);
  }
);
