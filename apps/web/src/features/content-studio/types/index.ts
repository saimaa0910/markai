/**
 * Content Studio Feature Types.
 */

export type ContentType = 'BLOG' | 'LANDING_PAGE' | 'EMAIL' | 'SOCIAL_POST' | 'AD_COPY';

export interface ContentItem {
  id: string;
  type: ContentType;
  title: string;
  body: string;
  status: 'DRAFT' | 'REVIEW' | 'PUBLISHED';
  target_audience?: string;
  created_at: string;
}

export interface GenerateContentPayload {
  type: ContentType;
  prompt: string;
  brand_tone?: string;
}
