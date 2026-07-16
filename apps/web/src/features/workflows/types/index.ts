export type WorkflowTrigger = 
  | 'MANUAL' 
  | 'SCHEDULED' 
  | 'WEBHOOK' 
  | 'CAMPAIGN_EVENT' 
  | 'CRM_EVENT';

export type WorkflowStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';

export type ExecutionStatus = 
  | 'PENDING' 
  | 'RUNNING' 
  | 'COMPLETED' 
  | 'FAILED' 
  | 'CANCELLED' 
  | 'WAITING';

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string | null;
  status: WorkflowStatus;
  trigger: WorkflowTrigger;
  steps_definition: Record<string, any>[];
  cron_expression: string | null;
  webhook_config: Record<string, any> | null;
  max_retries: number;
  timeout_seconds: number;
  organization_id: string;
  created_at?: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  organization_id: string;
  triggered_by: string | null;
  status: ExecutionStatus;
  input_data: Record<string, any> | null;
  output_data: Record<string, any> | null;
  error_message: string | null;
  retry_count: number;
  latency_ms: number | null;
  created_at?: string;
}

export interface WorkflowStep {
  id: string;
  execution_id: string;
  organization_id: string;
  step_id: string;
  step_type: string;
  status: ExecutionStatus;
  input_data: Record<string, any> | null;
  output_data: Record<string, any> | null;
  error_message: string | null;
  latency_ms: number | null;
  created_at?: string;
}
