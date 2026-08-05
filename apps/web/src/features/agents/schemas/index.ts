/**
 * @file index.ts
 * @description Zod Validation Schemas for Agents feature.
 */

import { z } from 'zod';

export const agentSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  role: z.string().min(2, 'Role must be at least 2 characters'),
  model: z.string().default('gpt-4o'),
  systemPrompt: z.string().optional(),
});

export type AgentFormValues = z.infer<typeof agentSchema>;
