/**
 * @file index.ts
 * @description Zod Schemas for SEO feature.
 */

import { z } from 'zod';

export const keywordSchema = z.object({
  term: z.string().min(1, 'Keyword term is required'),
});

export type KeywordFormValues = z.infer<typeof keywordSchema>;
