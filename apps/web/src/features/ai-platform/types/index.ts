export type RequestType = 'chat' | 'content' | 'embeddings' | 'vision' | 'json';

export interface AIProvider {
  key: string;
  name: string;
  isConnected: boolean;
  isHealthy: boolean;
  status: 'connected' | 'disconnected';
  latency: number; // in seconds
  priority: number;
  availableModels: number;
  currentRequests: number;
  errorCount: number;
  cost: number;
  supportsStreaming: boolean;
  supportsVision: boolean;
  supportsJson: boolean;
  supportsToolCalling: boolean;
  contextWindow: number;
  lastSync: string;
}

export interface AIModel {
  id: string;
  provider: string;
  model_name: string;
  name: string;
  context_window: number;
  supports_streaming: boolean;
  supports_vision: boolean;
  supports_json: boolean;
  supports_images: boolean;
  supports_audio: boolean;
  supports_tool_calling: boolean;
  supports_embeddings: boolean;
  input_token_price: number;
  output_token_price: number;
  latency: number;
  priority: number;
  is_healthy: boolean;
  organization_id: string | null;
  is_favorite?: boolean;
}

export interface AIRoutingRule {
  id: string;
  request_type: RequestType;
  model_registry_id: string;
  is_active: boolean;
  organization_id: string | null;
}

export interface AITokenUsage {
  id: string;
  organization_id: string;
  user_id: string;
  provider: string;
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number;
  status: 'success' | 'failure';
  error_message: string | null;
  created_at: string;
}
