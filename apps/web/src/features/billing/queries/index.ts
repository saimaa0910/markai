/**
 * Billing React Query Hooks.
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { billingKeys } from './keys';
import { billingApi } from '../services/api';

export function useSubscription() {
  return useQuery({
    queryKey: billingKeys.subscription(),
    queryFn: billingApi.getSubscription,
  });
}

export function useBillingPlans() {
  return useQuery({
    queryKey: billingKeys.plans(),
    queryFn: billingApi.getPlans,
  });
}

export function useCreditBalance() {
  return useQuery({
    queryKey: billingKeys.credits(),
    queryFn: billingApi.getCredits,
  });
}

export function useInvoices() {
  return useQuery({
    queryKey: billingKeys.invoices(),
    queryFn: billingApi.getInvoices,
  });
}

export function useCheckout() {
  return useMutation({
    mutationFn: (planId: string) => billingApi.checkout(planId),
  });
}
