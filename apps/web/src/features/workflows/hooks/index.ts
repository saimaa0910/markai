'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';
import { useAuthStore } from '@/store/auth';
import { 
  WorkflowDefinition, 
  WorkflowExecution, 
  WorkflowStep 
} from '../types';

interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useWorkflows
// ─────────────────────────────────────────────────────────────────────────────
export function useWorkflows(page = 1, pageSize = 20) {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<PaginatedData<WorkflowDefinition>>({
    queryKey: ['workflows-list', activeOrg?.id, page, pageSize],
    queryFn: async () => {
      const res = await apiClient.get('/workflows/definitions', {
        params: { page, page_size: pageSize }
      });
      return res.data;
    },
    enabled: !!activeOrg,
  });

  const createMutation = useMutation({
    mutationFn: async (wf: Omit<WorkflowDefinition, 'id' | 'organization_id'>) => {
      const res = await apiClient.post('/workflows/definitions', wf);
      return res.data as WorkflowDefinition;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows-list'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<WorkflowDefinition> }) => {
      const res = await apiClient.patch(`/workflows/definitions/${id}`, data);
      return res.data as WorkflowDefinition;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['workflows-list'] });
      queryClient.invalidateQueries({ queryKey: ['workflow-details', variables.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.delete(`/workflows/definitions/${id}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows-list'] });
    },
  });

  return {
    workflows: query.data?.items || [],
    total: query.data?.total || 0,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    createWorkflow: createMutation,
    updateWorkflow: updateMutation,
    deleteWorkflow: deleteMutation,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useWorkflowDetails
// ─────────────────────────────────────────────────────────────────────────────
export function useWorkflowDetails(wfId: string | undefined) {
  const query = useQuery<WorkflowDefinition>({
    queryKey: ['workflow-details', wfId],
    queryFn: async () => {
      const res = await apiClient.get(`/workflows/definitions/${wfId}`);
      return res.data;
    },
    enabled: !!wfId,
  });

  return {
    workflow: query.data || null,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useWorkflowExecution
// ─────────────────────────────────────────────────────────────────────────────
export function useWorkflowExecution(wfId: string | undefined) {
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: async (inputData: Record<string, any> = {}) => {
      const res = await apiClient.post(`/workflows/definitions/${wfId}/execute`, {
        input_data: inputData
      });
      return res.data as WorkflowExecution;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflow-executions', wfId] });
      queryClient.invalidateQueries({ queryKey: ['execution-steps', data.id] });
    },
  });

  return {
    executeWorkflow: runMutation,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useWorkflowExecutions
// ─────────────────────────────────────────────────────────────────────────────
export function useWorkflowExecutions(workflowId?: string, page = 1, pageSize = 20) {
  const { activeOrg } = useAuthStore();
  const query = useQuery<PaginatedData<WorkflowExecution>>({
    queryKey: ['workflow-executions', activeOrg?.id, workflowId, page, pageSize],
    queryFn: async () => {
      const res = await apiClient.get('/workflows/executions', {
        params: {
          workflow_id: workflowId || undefined,
          page,
          page_size: pageSize,
        }
      });
      return res.data;
    },
    enabled: !!activeOrg,
  });

  return {
    executions: query.data?.items || [],
    total: query.data?.total || 0,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useExecutionSteps
// ─────────────────────────────────────────────────────────────────────────────
export function useExecutionSteps(execId: string | undefined) {
  const query = useQuery<WorkflowStep[]>({
    queryKey: ['execution-steps', execId],
    queryFn: async () => {
      const res = await apiClient.get(`/workflows/executions/${execId}/steps`);
      return res.data || [];
    },
    enabled: !!execId,
  });

  return {
    steps: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
