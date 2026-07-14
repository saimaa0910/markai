export interface Prompt {
  id: string;
  name: string;
  content: string;
  category?: string;
  tags?: string[];
  version: number;
  is_shared: boolean;
  is_favorite: boolean;
  created_at: string;
  organization_id: string;
  variables: string[];
}

export interface PromptVersion {
  id: string;
  name: string;
  content: string;
  version: number;
  comment?: string;
  created_by?: string;
  created_at: string;
}

export interface PromptTestingResult {
  id: string;
  provider: string;
  model: string;
  prompt_name: string;
  variables_used: Record<string, string>;
  output: string;
  latency_ms: number;
  tokens_used: number;
  cost_usd: number;
  created_at: string;
}
