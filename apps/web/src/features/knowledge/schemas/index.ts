/**
 * @file index.ts
 * @description Zod Schemas for Knowledge feature.
 */

import { z } from 'zod';

export const knowledgeDocumentSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  category: z.string().default('General'),
});

export type KnowledgeDocumentFormValues = z.infer<typeof knowledgeDocumentSchema>;
