import { create } from 'zustand';

export interface AIProvider {
  id: string;
  name: string;
  provider: string;
  model_name: string;
  is_healthy: boolean;
  priority: number;
  cost_per_1k_input_tokens: number;
  cost_per_1k_output_tokens: number;
  max_tokens: number;
  context_window: number;
}

export interface AIRoutingRule {
  id: string;
  organization_id: string | null;
  request_type: string;
  primary_model_id: string;
  fallback_model_id: string | null;
  priority: number;
  is_active: boolean;
}

export interface AIUsageRecord {
  id: string;
  organization_id: string;
  model_id: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number;
  provider: string;
  model_name: string;
  created_at: string;
}

interface AIState {
  selectedProvider: string | null;
  setSelectedProvider: (provider: string | null) => void;
  selectedTimeRange: '24h' | '7d' | '30d' | '90d';
  setSelectedTimeRange: (range: '24h' | '7d' | '30d' | '90d') => void;
}

export const useAIStore = create<AIState>((set) => ({
  selectedProvider: null,
  setSelectedProvider: (selectedProvider) => set({ selectedProvider }),
  selectedTimeRange: '7d',
  setSelectedTimeRange: (selectedTimeRange) => set({ selectedTimeRange }),
}));
