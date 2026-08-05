/**
 * @file index.ts
 * @description Zod Schemas for AI Platform configuration.
 */

import { z } from 'zod';

export const aiProviderSchema = z.object({
  name: z.string().min(1, 'Provider name is required'),
  apiKey: z.string().min(1, 'API Key is required'),
  baseUrl: z.string().url().optional(),
});

export type AIProviderFormValues = z.infer<typeof aiProviderSchema>;
