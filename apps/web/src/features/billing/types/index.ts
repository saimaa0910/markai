/**
 * Billing & Subscription Feature Types.
 * @see apps/api/src/api/models/billing.py
 */

export interface BillingPlan {
  id: string;
  name: string;
  code: string;
  description: string | null;
  price_monthly: number;
  price_yearly: number;
  included_credits: number;
  is_active: boolean;
  features: string[];
}

export interface Subscription {
  id: string;
  organization_id: string;
  plan_id: string;
  status: 'ACTIVE' | 'PAST_DUE' | 'CANCELED' | 'TRIALING';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  plan?: BillingPlan;
}

export interface CreditBalance {
  total_credits: number;
  used_credits: number;
  remaining_credits: number;
}

export interface Invoice {
  id: string;
  number: string;
  amount: number;
  currency: string;
  status: 'PAID' | 'OPEN' | 'VOID' | 'UNCOLLECTIBLE';
  created_at: string;
  pdf_url?: string | null;
}
