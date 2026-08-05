/**
 * @file request.ts
 * @description CRM API Request Schemas.
 */

import { z } from 'zod';

export const contactRequestSchema = z.object({
  firstName: z.string().min(1),
  lastName: z.string().min(1),
  email: z.string().email(),
});
