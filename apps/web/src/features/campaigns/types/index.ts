/**
 * Campaign Feature Types — Mapped 1:1 to backend Pydantic schemas.
 * @see apps/api/src/api/schemas/campaign.py
 */

export type CampaignStatus = 'DRAFT' | 'SCHEDULED' | 'RUNNING' | 'COMPLETED' | 'PAUSED' | 'FAILED';
export type CampaignChannel = 'EMAIL' | 'SMS' | 'SOCIAL_AD' | 'BLOG' | 'WEBHOOK';

export interface CampaignTemplate {
  id: string;
  title: string;
  subject: string | null;
  content_a: string;
  content_b: string | null;
  campaign_id: string;
  organization_id: string;
}

export interface CampaignAnalytics {
  id: string;
  campaign_id: string;
  impressions_a: number;
  clicks_a: number;
  conversions_a: number;
  impressions_b: number;
  clicks_b: number;
  conversions_b: number;
  revenue: number;
  organization_id: string;
}

export interface Campaign {
  id: string;
  title: string;
  description: string | null;
  budget: number;
  channel: CampaignChannel;
  status: CampaignStatus;
  scheduled_for: string | null;
  organization_id: string;
  created_at: string;
  updated_at: string;
  template?: CampaignTemplate | null;
  analytics?: CampaignAnalytics | null;
}

export interface CampaignCreate {
  title: string;
  description?: string | null;
  budget?: number;
  channel: CampaignChannel;
  scheduled_for?: string | null;
  template: {
    title: string;
    subject?: string | null;
    content_a: string;
    content_b?: string | null;
  };
}

export interface CampaignUpdate {
  title?: string;
  description?: string | null;
  budget?: number;
  channel?: CampaignChannel;
  status?: CampaignStatus;
  scheduled_for?: string | null;
}

export interface CampaignTrackRequest {
  variant: 'A' | 'B';
  event_type: 'impression' | 'click' | 'conversion';
  revenue_generated?: number;
}
