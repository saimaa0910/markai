/**
 * Social Studio Schemas (Zod) — Sprint 7.5
 */
import { z } from 'zod';

export const SocialGenerateSchema = z.object({
  platform: z.string().min(1, 'Platform is required'),
  content_type: z.string().min(1, 'Content type is required'),
  prompt: z
    .string()
    .min(10, 'Prompt must be at least 10 characters')
    .max(5000, 'Prompt cannot exceed 5000 characters'),
  target_audience: z.string().optional(),
  keywords: z.array(z.string()).optional(),
  generate_image: z.boolean().optional(),
  image_style: z.string().optional(),
  translate_to: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
  run_reflection: z.boolean().optional(),
  run_evaluation: z.boolean().optional(),
});

export const SocialScheduleSchema = z.object({
  post_run_id: z.string().min(1),
  platform: z.string().min(1),
  schedule_type: z.enum(['PUBLISH_NOW', 'SCHEDULED', 'RECURRING', 'BULK', 'DRAFT', 'QUEUE']),
  scheduled_at: z.string().optional(),
  timezone: z.string().optional(),
  auto_publish: z.boolean().optional(),
});

export const SocialPublishSchema = z.object({
  post_run_id: z.string().min(1),
  platform: z.string().min(1),
  override_content: z.string().optional(),
  image_url: z.string().url().optional(),
});

export const SocialReplySchema = z.object({
  platform: z.string().min(1),
  original_post: z.string().min(1, 'Original post is required'),
  engagement_type: z.enum(['REPLY', 'COMMENT', 'DM_DRAFT', 'COMMUNITY_REPLY', 'FAQ_REPLY', 'THANK_YOU']),
  brand_voice_override: z.string().optional(),
});

export const SocialHashtagSchema = z.object({
  platform: z.string().min(1),
  keywords: z.array(z.string()).optional(),
  industry: z.string().optional(),
  brand_name: z.string().optional(),
  campaign_name: z.string().optional(),
  location: z.string().optional(),
  max_count: z.number().min(1).max(30).optional(),
});

export type SocialGenerateFormValues = z.infer<typeof SocialGenerateSchema>;
export type SocialScheduleFormValues = z.infer<typeof SocialScheduleSchema>;
export type SocialReplyFormValues = z.infer<typeof SocialReplySchema>;
