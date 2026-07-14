import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = typeof window !== 'undefined' 
  ? (window.location.hostname === 'localhost' ? 'http://localhost:8000/api/v1' : '/api/v1')
  : 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach access token
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
        } catch (e) {
          console.error('Failed to parse auth token from storage', e);
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
            
            // Save back to Zustand storage format
            parsed.state.accessToken = access_token;
            parsed.state.refreshToken = refresh_token;
            localStorage.setItem('eaimos-auth-storage', JSON.stringify(parsed));
            
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
    return Promise.reject(error);
  }
);
