export type AgentType = 
  | 'MARKETING' 
  | 'CONTENT' 
  | 'CAMPAIGN' 
  | 'CRM' 
  | 'ANALYTICS' 
  | 'RESEARCH' 
  | 'SEO' 
  | 'WORKFLOW' 
  | 'CUSTOM';

export type AgentStatus = 'ACTIVE' | 'INACTIVE' | 'ARCHIVED';

export type AgentRunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface AgentDefinition {
  id: string;
  name: string;
  description: string | null;
  agent_type: AgentType;
  status: AgentStatus;
  system_prompt: string | null;
  prompt_template_name: string | null;
  allowed_tools: string[];
  preferred_model: string | null;
  temperature: number;
  max_tokens: number | null;
  memory_enabled: boolean;
  max_memory_items: number;
  max_iterations: number;
  is_public: boolean;
  organization_id: string;
  avatar_color?: string; // visual tag helper
  avatar_icon?: string; // visual tag helper
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
