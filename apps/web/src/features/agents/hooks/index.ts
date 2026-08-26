'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';
import { useAuthStore } from '@/store/auth';
import { 
  AgentDefinition, 
  AgentSession, 
  AgentRun, 
  AgentLog 
} from '../types';

const EMPTY_ITEMS: any[] = [];
const EMPTY_LOGS: AgentLog[] = [];

// Helper: Custom paginated response container
interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useAgents
// ─────────────────────────────────────────────────────────────────────────────
export function useAgents(page = 1, pageSize = 20) {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<PaginatedData<AgentDefinition>>({
    queryKey: ['agents-list', activeOrg?.id, page, pageSize],
    queryFn: async () => {
      const res = await apiClient.get('/agents/definitions', {
        params: { page, page_size: pageSize }
      });
      return res.data;
    },
    enabled: !!activeOrg,
  });

  const createMutation = useMutation({
    mutationFn: async (agent: Omit<AgentDefinition, 'id' | 'organization_id'>) => {
      const res = await apiClient.post('/agents/definitions', agent);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<AgentDefinition> }) => {
      const res = await apiClient.patch(`/agents/definitions/${id}`, data);
      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
      queryClient.invalidateQueries({ queryKey: ['agent-details', variables.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.delete(`/agents/definitions/${id}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
    },
  });

  return {
    agents: query.data?.items ?? EMPTY_ITEMS,
    total: query.data?.total || 0,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    createAgent: createMutation,
    updateAgent: updateMutation,
    deleteAgent: deleteMutation,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useAgentDetails
// ─────────────────────────────────────────────────────────────────────────────
export function useAgentDetails(agentId: string | undefined) {
  const query = useQuery<AgentDefinition>({
    queryKey: ['agent-details', agentId],
    queryFn: async () => {
      const res = await apiClient.get(`/agents/definitions/${agentId}`);
      return res.data;
    },
    enabled: !!agentId,
  });

  return {
    agent: query.data || null,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useAgentSessions
// ─────────────────────────────────────────────────────────────────────────────
export function useAgentSessions(page = 1, pageSize = 20) {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<PaginatedData<AgentSession>>({
    queryKey: ['agent-sessions', activeOrg?.id, page, pageSize],
    queryFn: async () => {
      const res = await apiClient.get('/agents/sessions', {
        params: { page, page_size: pageSize }
      });
      return res.data;
    },
    enabled: !!activeOrg,
  });

  const createMutation = useMutation({
    mutationFn: async (session: Omit<AgentSession, 'id' | 'user_id' | 'organization_id' | 'is_active'>) => {
      const res = await apiClient.post('/agents/sessions', session);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-sessions'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<AgentSession> }) => {
      const res = await apiClient.patch(`/agents/sessions/${id}`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-sessions'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.delete(`/agents/sessions/${id}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-sessions'] });
    },
  });

  return {
    sessions: query.data?.items ?? EMPTY_ITEMS,
    total: query.data?.total || 0,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    createSession: createMutation,
    updateSession: updateMutation,
    deleteSession: deleteMutation,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useAgentRuns
// ─────────────────────────────────────────────────────────────────────────────
export function useAgentRuns(sessionId: string | undefined, page = 1, pageSize = 20) {
  const query = useQuery<PaginatedData<AgentRun>>({
    queryKey: ['agent-runs', sessionId, page, pageSize],
    queryFn: async () => {
      const res = await apiClient.get(`/agents/sessions/${sessionId}/runs`, {
        params: { page, page_size: pageSize }
      });
      return res.data;
    },
    enabled: !!sessionId,
  });

  return {
    runs: query.data?.items ?? EMPTY_ITEMS,
    total: query.data?.total || 0,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useRunLogs
// ─────────────────────────────────────────────────────────────────────────────
export function useRunLogs(runId: string | undefined) {
  const query = useQuery<AgentLog[]>({
    queryKey: ['run-logs', runId],
    queryFn: async () => {
      const res = await apiClient.get(`/agents/runs/${runId}/logs`);
      return res.data || EMPTY_LOGS;
    },
    enabled: !!runId,
  });

  return {
    logs: query.data ?? EMPTY_LOGS,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useAgentExecution
// ─────────────────────────────────────────────────────────────────────────────
export function useAgentExecution(sessionId: string | undefined) {
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: async (userInput: string) => {
      const res = await apiClient.post(`/agents/sessions/${sessionId}/run`, {
        user_input: userInput
      });
      return res.data as AgentRun;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['agent-runs', sessionId] });
      queryClient.invalidateQueries({ queryKey: ['run-logs', data.id] });
    },
  });

  return {
    runAgent: runMutation,
  };
}
