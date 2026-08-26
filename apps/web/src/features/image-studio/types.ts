export interface ImageGenerateRequest {
  prompt: string;
  style?: string;
  aspect_ratio?: string;
  negative_prompt?: string;
  campaign_id?: string;
  knowledge_collections?: string[];
  model?: string;
  seed?: number;
  steps?: number;
  cfg_scale?: number;
  agent_id?: string;
}

export interface ImageEditRequest {
  image_url: string;
  prompt: string;
  mask_url?: string;
  style?: string;
  model?: string;
}

export interface ImageVariationRequest {
  image_url: string;
  style?: string;
  model?: string;
}

export interface ImageUpscaleRequest {
  image_url: string;
  scale?: number;
}

export interface ImageBackgroundRemoveRequest {
  image_url: string;
}

export interface ImageBackgroundReplaceRequest {
  image_url: string;
  background_prompt: string;
}

export interface ImageInpaintRequest {
  image_url: string;
  mask_url: string;
  prompt: string;
}

export interface ImageOutpaintRequest {
  image_url: string;
  mask_url: string;
  prompt: string;
}

export interface ImageReflectionScores {
  composition: number;
  brand_alignment: number;
  readability: number;
  accessibility: number;
  contrast: number;
  creativity: number;
  marketing_impact: number;
  visual_hierarchy: number;
  cta_visibility: number;
}

export interface ImageReflectionResult {
  is_satisfactory: boolean;
  critique: string;
  suggested_edits: string;
  scores: ImageReflectionScores;
}

export interface ImageEvaluationMetrics {
  marketing_score: number;
  brand_score: number;
  accessibility: number;
  image_quality: number;
  creativity: number;
  composition: number;
  seo_score: number;
  engagement_score: number;
  overall_score: number;
  passed: boolean;
  critique: string;
}

export interface ImageResponse {
  id: string;
  status?: string;
  storage_url: string;
  provider: string;
  model: string;
  prompt: string;
  compiled_prompt?: string;
  reflection?: ImageReflectionResult;
  evaluation?: ImageEvaluationMetrics;
  error?: {
    code?: string;
    message: string;
    details?: Record<string, any>;
  };
}

export interface ImageHistoryItem {
  id: string;
  prompt: string;
  negative_prompt?: string;
  provider: string;
  model: string;
  seed?: number;
  cfg_scale?: number;
  steps?: number;
  storage_url: string;
  tags?: Record<string, any>;
  meta_data?: Record<string, any>;
  created_at: string;
  campaign_id?: string;
  run_id?: string;
}

export interface ImageProvider {
  name: string;
  label: string;
  priority: number;
  configured: boolean;
}

export interface ImageModel {
  name: string;
  label: string;
  provider: string;
  supported_ratios: string[];
}
