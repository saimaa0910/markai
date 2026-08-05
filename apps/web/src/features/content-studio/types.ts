/**
 * Content Studio Types — Sprint 7.2
 */

export type ContentType =
  | 'BLOG_ARTICLE'
  | 'LANDING_PAGE'
  | 'PRODUCT_PAGE'
  | 'FEATURE_PAGE'
  | 'DOCUMENTATION'
  | 'FAQ'
  | 'CASE_STUDY'
  | 'WHITEPAPER'
  | 'EMAIL_CAMPAIGN'
  | 'COLD_EMAIL'
  | 'NEWSLETTER'
  | 'LINKEDIN_POST'
  | 'TWITTER_POST'
  | 'INSTAGRAM_CAPTION'
  | 'FACEBOOK_POST'
  | 'GOOGLE_AD'
  | 'FACEBOOK_AD'
  | 'HEADLINE'
  | 'TAGLINE'
  | 'CTA'
  | 'META_TITLE'
  | 'META_DESCRIPTION'
  | 'VIDEO_SCRIPT'
  | 'PODCAST_SCRIPT'
  | 'YOUTUBE_DESCRIPTION'
  | 'IMAGE_PROMPT';

export type ImprovementType =
  | 'REWRITE'
  | 'SUMMARIZE'
  | 'EXPAND'
  | 'SHORTEN'
  | 'IMPROVE_GRAMMAR'
  | 'IMPROVE_SEO'
  | 'IMPROVE_READABILITY'
  | 'IMPROVE_BRAND_VOICE'
  | 'TRANSLATE'
  | 'TONE_CONVERSION'
  | 'AUDIENCE_CONVERSION';

export interface ContentGenerateRequest {
  content_type: ContentType;
  prompt: string;
  brand_voice_override?: string;
  forbidden_words?: string[];
  preferred_words?: string[];
  knowledge_collections?: string[];
  target_audience?: string;
  keywords?: string[];
  preferred_model?: string;
  temperature?: number;
  run_reflection?: boolean;
  run_evaluation?: boolean;
}

export interface ContentImproveRequest {
  content: string;
  improvement_type: ImprovementType;
  target_tone?: string;
  target_audience?: string;
  target_language?: string;
  keywords?: string[];
  preferred_model?: string;
  temperature?: number;
}

export interface ContentSEOMetrics {
  title_length_ok: boolean;
  description_length_ok: boolean;
  keyword_density: Record<string, number>;
  keyword_density_ok: boolean;
  heading_hierarchy_ok: boolean;
  readability_score: number;
  readability_level: 'EASY' | 'MEDIUM' | 'DIFFICULT';
  internal_links_count: number;
  external_links_count: number;
  seo_score: number;
  suggestions: string[];
}

export interface ContentResponse {
  title: string;
  generated_content: string;
  plan?: Record<string, any>;
  tool_calls?: Record<string, any>[];
  total_tokens: number;
  latency_ms: number;
  cost_usd: number;
  seo_metrics?: ContentSEOMetrics;
  overall_score?: number;
  reflection_passed: boolean;
  critique?: string;
  suggested_edits?: string;
}

export interface ContentTemplate {
  id: string;
  name: string;
  description: string;
  content_type: ContentType;
  template_text: string;
  required_variables: string[];
}

export interface ContentHistoryItem {
  run_id: string;
  created_at: string | null;
  status: string;
  user_input: string;
  latency_ms: number;
  tokens: number;
  output_preview: string;
}
