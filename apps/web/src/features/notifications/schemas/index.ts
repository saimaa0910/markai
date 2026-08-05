/**
 * @file index.ts
 * @description Zod Schemas for Notifications feature.
 */

import { z } from 'zod';

export const notificationPreferenceSchema = z.object({
  emailAlerts: z.boolean().default(true),
  pushAlerts: z.boolean().default(false),
  digestFrequency: z.enum(['realtime', 'daily', 'weekly']).default('daily'),
});

export type NotificationPreferenceValues = z.infer<typeof notificationPreferenceSchema>;
