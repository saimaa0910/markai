export type AgentType = 
  | 'MARKETING' 
  | 'CONTENT' 
  | 'CAMPAIGN' 
  | 'CRM' 
  | 'ANALYTICS' 
  | 'RESEARCH' 
  | 'SEO' 
  | 'WORKFLOW' 
  | 'CUSTOM'
  | 'SALES'
  | 'SUPPORT'
  | 'IMAGE'
  | 'SOCIAL';

export type AgentStatus = 'ACTIVE' | 'INACTIVE' | 'ARCHIVED';

export type AgentRunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type MemoryType = 'SHORT_TERM' | 'LONG_TERM' | 'EPISODIC' | 'SEMANTIC';

export interface AgentDefinition {
  id: string;
  name: string;
  description: string | null;
  agent_type: AgentType;
  status: AgentStatus;
  system_prompt: string | null;
  prompt_template_name: string | null;
  allowed_tools: string[];
  preferred_provider?: string | null;
  preferred_model?: string | null;
  temperature?: number;
  top_p?: number | null;
  max_tokens?: number | null;
  reasoning_mode?: string | null;
  execution_mode?: string | null;
  memory_enabled: boolean;
  max_memory_items: number;
  max_iterations: number;
  is_public: boolean;
  is_favorite?: boolean;
  is_pinned?: boolean;
  organization_id: string;
  avatar?: string | null;
  avatar_color?: string | null;
  welcome_message?: string | null;
}

export interface AgentSession {
  id: string;
  agent_id: string;
  title: string;
  context: Record<string, any> | null;
  user_id: string;
  organization_id: string;
  is_active: boolean;
}

export interface AgentRun {
  id: string;
  session_id: string;
  organization_id: string;
  user_input: string;
  agent_output: string | null;
  plan: Record<string, any> | null;
  tool_calls: Record<string, any>[] | null;
  status: AgentRunStatus;
  error_message: string | null;
  iterations: number;
  total_tokens: number;
  latency_ms: number | null;
}

export interface AgentLog {
  id: string;
  run_id: string;
  organization_id: string;
  level: string;
  step_type: string;
  content: string;
  meta_data: Record<string, any> | null;
}

export interface ToolExecution {
  step_id?: string;
  tool_name: string;
  success: boolean;
  output: any;
  error: string | null;
  tool_params?: Record<string, any>;
  latency_ms?: number;
}

export interface AgentMemoryItem {
  id: string;
  memory_key: string;
  memory_value: string;
  memory_type: MemoryType;
  importance: number;
  access_count: number;
}

export interface AgentEvaluation {
  id: string;
  run_id: string;
  organization_id: string;
  accuracy_score: number | null;
  cost_score: number | null;
  latency_score: number | null;
  reasoning_score: number | null;
  tool_usage_score: number | null;
  knowledge_usage_score: number | null;
  brand_alignment_score: number | null;
  safety_score: number | null;
  hallucination_score: number | null;
  grammar_score: number | null;
  tone_score: number | null;
  completeness_score: number | null;
  overall_score: number | null;
  confidence: number | null;
  critique: string | null;
  suggested_edits: string | null;
  is_satisfactory: boolean;
}

export interface AgentToolInfo {
  name: string;
  description: string;
  category?: string;
  parameters_schema?: Record<string, any>;
}

export interface AgentChatRequest {
  user_input: string;
  session_title?: string;
  run_reflection?: boolean;
  run_evaluation?: boolean;
}

export interface AgentStreamRequest {
  user_input: string;
  session_id?: string;
  session_title?: string;
  run_reflection?: boolean;
  run_evaluation?: boolean;
  conversation_history?: Array<{ role: string; content: string }>;
}

// SSE Event types emitted by the streaming runtime
export type AgentStreamEventType =
  | 'agent_start'
  | 'context_ready'
  | 'plan'
  | 'tool_call'
  | 'tool_result'
  | 'token'
  | 'reflection'
  | 'evaluation'
  | 'status'
  | 'done'
  | 'error';

export interface AgentStreamEvent {
  type: AgentStreamEventType;
  data: Record<string, any>;
}

export type AgentConfig = AgentDefinition;
