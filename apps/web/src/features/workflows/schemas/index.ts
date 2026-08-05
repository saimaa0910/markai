/**
 * @file index.ts
 * @description Zod Schemas for Workflows feature.
 */

import { z } from 'zod';

export const workflowSchema = z.object({
  name: z.string().min(1, 'Workflow name is required'),
  description: z.string().optional(),
  triggerType: z.enum(['manual', 'scheduled', 'webhook']).default('manual'),
});

export type WorkflowFormValues = z.infer<typeof workflowSchema>;
