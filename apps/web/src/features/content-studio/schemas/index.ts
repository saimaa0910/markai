/**
 * @file index.ts
 * @description Zod Schemas for Content Studio.
 */

import { z } from 'zod';

export const contentItemSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  contentType: z.enum(['blog', 'landing-page', 'social', 'email', 'ad']),
  body: z.string().min(10, 'Content body must be at least 10 characters'),
});

export type ContentItemFormValues = z.infer<typeof contentItemSchema>;
