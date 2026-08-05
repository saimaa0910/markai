/**
 * @file index.ts
 * @description Zod Schemas for Prompts feature.
 */

import { z } from 'zod';

export const promptTemplateSchema = z.object({
  title: z.string().min(1, 'Prompt title is required'),
  template: z.string().min(5, 'Template content must be at least 5 characters'),
  variables: z.array(z.string()).default([]),
});

export type PromptTemplateFormValues = z.infer<typeof promptTemplateSchema>;
