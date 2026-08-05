/**
 * Analytics API Service Client.
 */

import { apiClient } from '@/services/api-client';
import type { AnalyticsOverview } from '../types';

export const analyticsApi = {
  getOverview: () => apiClient.get<AnalyticsOverview>('/analytics/overview').then(r => r.data),
};
