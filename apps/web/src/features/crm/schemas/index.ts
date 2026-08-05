/**
 * @file index.ts
 * @description Zod Schemas for CRM Feature.
 */

import { z } from 'zod';

export const contactSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  phone: z.string().optional(),
});

export type ContactFormValues = z.infer<typeof contactSchema>;
