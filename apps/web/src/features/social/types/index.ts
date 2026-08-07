/**
 * Social Studio Types — Sprint 7.5
 * ==================================
 * TypeScript interfaces matching the Social Agent backend schemas.
 */

export type SocialPlatform =
  | 'LINKEDIN'
  | 'TWITTER'
  | 'FACEBOOK'
  | 'INSTAGRAM'
  | 'THREADS'
  | 'PINTEREST'
  | 'TIKTOK'
  | 'YOUTUBE_COMMUNITY'
  | 'YOUTUBE_SHORTS'
  | 'REDDIT'
  | 'DISCORD'
  | 'TELEGRAM'
  | 'MEDIUM'
  | 'QUORA';

export type SocialContentType =
  | 'POST'
  | 'THREAD'
  | 'CAROUSEL'
  | 'STORY'
  | 'REEL'
  | 'SHORT'
  | 'ANNOUNCEMENT'
  | 'LAUNCH_POST'
  | 'CASE_STUDY'
  | 'TESTIMONIAL'
  | 'POLL'
  | 'QUESTION'
  | 'MEME'
  | 'EDUCATIONAL'
  | 'PRODUCT_UPDATE'
  | 'HIRING_POST'
  | 'COMMUNITY_POST'
  | 'NEWSLETTER_PROMO'
  | 'EVENT_PROMO'
  | 'BLOG_PROMO';

export type ScheduleType = 'PUBLISH_NOW' | 'SCHEDULED' | 'RECURRING' | 'BULK' | 'DRAFT' | 'QUEUE';

export type SocialPostStatus = 'DRAFT' | 'SCHEDULED' | 'PUBLISHED' | 'FAILED' | 'QUEUED' | 'CANCELLED';

export type EngagementType = 'REPLY' | 'COMMENT' | 'DM_DRAFT' | 'COMMUNITY_REPLY' | 'FAQ_REPLY' | 'THANK_YOU';

// ─── Sub-models ───────────────────────────────────────────────────────────────

export interface HashtagItem {
  tag: string;
  category: string;
  reach_score: number;
}

export interface HashtagResult {
  hashtags: HashtagItem[];
  hashtag_string: string;
  total_count: number;
  estimated_reach: number;
  categories: Record<string, string[]>;
}

export interface PlatformOptimizationResult {
  optimized_content: string;
  platform: string;
  tone: string;
  char_used: number;
  char_limit: number;
  char_remaining: number;
  within_limit: boolean;
  best_practices: string[];
}

export interface SocialReflectionResult {
  is_satisfactory: boolean;
  platform_compliant: boolean;
  brand_compliant: boolean;
  readability_ok: boolean;
  engagement_score: number;
  cta_quality: number;
  hook_quality: number;
  formatting_ok: boolean;
  critique: string | null;
  suggested_edits: string | null;
}

export interface SocialEvaluationResult {
  brand_score: number;
  engagement_score: number;
  platform_score: number;
  readability: number;
  seo_score: number;
  viral_potential: number;
  confidence: number;
  overall_score: number;
  passed: boolean;
  critique: string | null;
}

export interface ScheduleMetadata {
  schedule_type: ScheduleType;
  scheduled_at?: string | null;
  timezone?: string;
  recurring_pattern?: string | null;
}

export interface SocialPostContent {
  caption: string | null;
  headline: string | null;
  cta: string | null;
  hook: string | null;
  body: string | null;
  summary: string | null;
  thread_parts: string[] | null;
  raw_content: string;
}

// ─── Request Types ────────────────────────────────────────────────────────────

export interface SocialGenerateRequest {
  platform: SocialPlatform;
  content_type: SocialContentType;
  prompt: string;
  target_audience?: string;
  keywords?: string[];
  campaign_id?: string;
  brand_voice_override?: string;
  knowledge_collections?: string[];
  generate_image?: boolean;
  image_style?: string;
  translate_to?: string;
  schedule?: ScheduleMetadata;
  preferred_model?: string;
  temperature?: number;
  run_reflection?: boolean;
  run_evaluation?: boolean;
  agent_id?: string;
}

export interface SocialStreamRequest extends SocialGenerateRequest {
  session_id?: string;
  session_title?: string;
}

export interface SocialScheduleRequest {
  post_run_id: string;
  platform: SocialPlatform;
  schedule: ScheduleMetadata;
  auto_publish?: boolean;
}

export interface SocialPublishRequest {
  post_run_id: string;
  platform: SocialPlatform;
  override_content?: string;
  image_url?: string;
}

export interface SocialReplyRequest {
  platform: SocialPlatform;
  original_post: string;
  engagement_type: EngagementType;
  brand_voice_override?: string;
  preferred_model?: string;
  temperature?: number;
}

export interface SocialOptimizeRequest {
  content: string;
  platform: SocialPlatform;
  hashtag_string?: string;
  cta?: string;
  hook?: string;
}

export interface SocialHashtagRequest {
  platform: SocialPlatform;
  keywords?: string[];
  industry?: string;
  brand_name?: string;
  campaign_name?: string;
  location?: string;
  max_count?: number;
}

// ─── Response Types ───────────────────────────────────────────────────────────

export interface SocialPostResponse {
  run_id?: string;
  platform: string;
  content_type: string;
  content: SocialPostContent;
  image_url?: string | null;
  hashtags?: HashtagResult | null;
  optimization?: PlatformOptimizationResult | null;
  reflection?: SocialReflectionResult | null;
  evaluation?: SocialEvaluationResult | null;
  plan?: Record<string, any> | null;
  schedule?: ScheduleMetadata | null;
  total_tokens: number;
  latency_ms: number;
  cost_usd: number;
}

export interface SocialScheduleResponse {
  run_id: string;
  platform: string;
  status: SocialPostStatus;
  scheduled_at?: string | null;
  schedule_type: ScheduleType;
  message: string;
}

export interface SocialPublishResponse {
  run_id: string;
  platform: string;
  status: string;
  published: boolean;
  message: string;
  platform_post_id?: string | null;
}

export interface SocialReplyResponse {
  engagement_type: string;
  platform: string;
  reply_content: string;
  total_tokens: number;
  latency_ms: number;
}

export interface SocialPlatformInfo {
  platform: string;
  char_limit: number;
  hashtag_limit: number;
  tone: string;
  emoji_friendly: boolean;
  supports_images: boolean;
  supports_video: boolean;
  supports_carousel: boolean;
  supports_polls: boolean;
  best_practices: string[];
  image_ratio?: string | null;
}

export interface SocialHistoryItem {
  run_id: string;
  platform: string;
  content_type: string;
  status: string;
  output_preview: string;
  image_url?: string | null;
  latency_ms?: number | null;
  tokens: number;
  created_at?: string | null;
  scheduled_at?: string | null;
}

export interface SocialTemplate {
  id: string;
  name: string;
  content_type: SocialContentType;
  description: string;
  platforms: string[];
  example_prompt: string;
}

export interface SocialQueueItem {
  run_id: string;
  platform: string;
  content_type: string;
  status: string;
  scheduled_at?: string | null;
  preview: string;
}

export interface SocialQueueResponse {
  queue: SocialQueueItem[];
  total: number;
  draft_count: number;
  scheduled_count: number;
}

export interface SocialAnalyticsResponse {
  platform?: string | null;
  total_posts: number;
  avg_tokens: number;
  avg_latency_ms: number;
  top_content_types: string[];
  recent_runs: Record<string, any>[];
}

export interface SocialCalendarResponse {
  view: string;
  entries: Record<string, any>[];
  total_posts: number;
}

// ─── SSE Event Types ──────────────────────────────────────────────────────────

export type SocialStreamEventType =
  | 'agent_start'
  | 'planning'
  | 'brand'
  | 'campaign'
  | 'knowledge'
  | 'content'
  | 'image'
  | 'hashtags'
  | 'optimization'
  | 'reflection'
  | 'evaluation'
  | 'schedule'
  | 'publish'
  | 'completed'
  | 'llm_token'
  | 'status'
  | 'error';

export interface SocialStreamEvent {
  type: SocialStreamEventType;
  data: Record<string, any>;
}

// ─── Studio State ─────────────────────────────────────────────────────────────

export interface SocialStudioState {
  platform: SocialPlatform;
  contentType: SocialContentType;
  prompt: string;
  targetAudience: string;
  keywords: string[];
  brandVoice: string;
  generateImage: boolean;
  imageStyle: string;
  scheduleType: ScheduleType;
  scheduledAt: string | null;
  campaignId: string | null;
  provider: string;
  temperature: number;
}
