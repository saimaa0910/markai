/**
 * @file index.ts
 * @description Zod Schemas for Billing feature.
 */

import { z } from 'zod';

export const checkoutSchema = z.object({
  planId: z.string().min(1, 'Plan ID is required'),
  paymentMethodId: z.string().min(1, 'Payment Method is required'),
});

export type CheckoutFormValues = z.infer<typeof checkoutSchema>;
