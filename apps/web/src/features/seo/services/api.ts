/**
 * SEO API Service Client.
 */

import { apiClient } from '@/services/api-client';
import type { SEODashboardData, KeywordMetric } from '../types';

export const seoApi = {
  getOverview: () => apiClient.get<SEODashboardData>('/seo/overview').then(r => r.data),
  addKeyword: (keyword: string) => apiClient.post<KeywordMetric>('/seo/keywords', { keyword }).then(r => r.data),
  runAudit: (domain: string) => apiClient.post<{ status: string }>('/seo/audit', { domain }).then(r => r.data),
};
