/**
 * @file request.ts
 * @description Zod validation schema for organization request payloads.
 */

import { z } from 'zod';

export const organizationRequestSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  slug: z.string().min(2, 'Slug must be at least 2 characters').regex(/^[a-z0-9-]+$/, 'Slug can only contain lowercase letters, numbers, and hyphens'),
});

export type OrganizationRequestFormValues = z.infer<typeof organizationRequestSchema>;
