/**
 * Billing API Service Client.
 */

import { apiClient } from '@/services/api-client';
import type { BillingPlan, Subscription, CreditBalance, Invoice } from '../types';

export const billingApi = {
  getSubscription: () => apiClient.get<Subscription>('/billing/subscription').then(r => r.data),
  getPlans: () => apiClient.get<BillingPlan[]>('/billing/plans').then(r => r.data),
  getCredits: () => apiClient.get<CreditBalance>('/billing/credits').then(r => r.data),
  getInvoices: () => apiClient.get<Invoice[]>('/billing/invoices').then(r => r.data),
  checkout: (planId: string) => apiClient.post<{ url: string }>('/billing/checkout', { plan_id: planId }).then(r => r.data),
};
