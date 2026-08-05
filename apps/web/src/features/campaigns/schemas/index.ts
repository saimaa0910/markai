/**
 * @file index.ts
 * @description Zod Schemas for Campaigns feature.
 */

import { z } from 'zod';

export const campaignSchema = z.object({
  name: z.string().min(1, 'Campaign name is required'),
  channels: z.array(z.string()).min(1, 'At least one channel must be selected'),
  budgetUsd: z.number().positive().optional(),
});

export type CampaignFormValues = z.infer<typeof campaignSchema>;
