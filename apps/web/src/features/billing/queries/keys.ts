/**
 * Billing Query Key Factory.
 */

export const billingKeys = {
  all: ['billing'] as const,
  subscription: () => [...billingKeys.all, 'subscription'] as const,
  plans: () => [...billingKeys.all, 'plans'] as const,
  credits: () => [...billingKeys.all, 'credits'] as const,
  invoices: () => [...billingKeys.all, 'invoices'] as const,
};
