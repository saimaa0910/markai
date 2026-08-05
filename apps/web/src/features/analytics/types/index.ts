/**
 * Analytics Platform Feature Types.
 * @see apps/api/src/api/models/analytics.py
 */

export interface AnalyticsOverview {
  total_revenue: number;
  active_leads: number;
  conversion_rate: number;
  total_ai_tokens: number;
  total_agent_runs: number;
  revenue_trend: { date: string; value: number }[];
  funnel_steps: { step_name: string; count: number; conversion_percent: number }[];
}

export interface FunnelStep {
  name: string;
  count: number;
  dropoff_rate: number;
}
