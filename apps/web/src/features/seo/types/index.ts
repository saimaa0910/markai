/**
 * SEO Platform Feature Types.
 */

export interface KeywordMetric {
  id: string;
  keyword: string;
  search_volume: number;
  difficulty: number;
  current_rank: number;
  intent: 'INFORMATIONAL' | 'COMMERCIAL' | 'TRANSACTIONAL' | 'NAVIGATIONAL';
  cpc: number;
}

export interface TechnicalAuditIssue {
  id: string;
  type: 'CRITICAL' | 'WARNING' | 'NOTICE';
  title: string;
  url: string;
  description: string;
}

export interface SEODashboardData {
  health_score: number;
  total_keywords: number;
  top_10_ranks: number;
  organic_traffic: number;
  keywords: KeywordMetric[];
  issues: TechnicalAuditIssue[];
}
