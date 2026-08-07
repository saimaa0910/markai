import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';
import { useAuthStore } from '@/store/auth';
import { useAIPlatformStore } from '../store/ai-platform';
import { AIModel, AIRoutingRule, AITokenUsage, AIProvider } from '../types';
import * as React from 'react';

// Meta data helper for providers
export const PROVIDER_META: Record<string, { label: string; logoUrl?: string; description: string }> = {
  openai: { label: 'OpenAI', description: 'Advanced reasoning models like GPT-4o and GPT-4o-mini.' },
  groq: { label: 'Groq', description: 'Ultra-low latency LPU inference engine for open models.' },
  anthropic: { label: 'Anthropic Claude', description: 'Highly precise reasoning, long context window.' },
  google: { label: 'Google Gemini', description: 'Multimodal processing and enormous context sizes.' },
  openrouter: { label: 'OpenRouter', description: 'Unified access gateway to hundreds of open-source LLMs.' },
  deepseek: { label: 'DeepSeek', description: 'Powerful intelligence and cheap reasoning models.' },
  mistral: { label: 'Mistral AI', description: 'State of the art open weights models from France.' },
  ollama: { label: 'Local Ollama', description: 'Secure local execution of large language models.' },
};

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Models
// ─────────────────────────────────────────────────────────────────────────────
export function useModels() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<AIModel[]>({
    queryKey: ['ai-models', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/models/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const toggleHealth = useMutation({
    mutationFn: async ({ modelId, isHealthy }: { modelId: string; isHealthy: boolean }) => {
      const res = await apiClient.patch(`/ai/models/${modelId}`, { is_healthy: isHealthy });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-models'] });
    },
  });

  const updatePriority = useMutation({
    mutationFn: async ({ modelId, priority }: { modelId: string; priority: number }) => {
      const res = await apiClient.patch(`/ai/models/${modelId}`, { priority });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-models'] });
    },
  });

  return {
    models: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    toggleHealth,
    updatePriority,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Providers
// ─────────────────────────────────────────────────────────────────────────────
export function useProviders() {
  const query = useQuery<any[]>({
    queryKey: ['ai-providers-dashboard'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers/');
      return res.data || [];
    },
  });

  return {
    providers: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Usage
// ─────────────────────────────────────────────────────────────────────────────
export function useUsage() {
  const { activeOrg } = useAuthStore();
  const query = useQuery<AITokenUsage[]>({
    queryKey: ['ai-usage', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/usage/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const usage = query.data || [];

  const kpis = React.useMemo(() => {
    const totalRequests = usage.length;
    const successfulRequests = usage.filter((u) => u.status === 'success').length;
    const failedRequests = totalRequests - successfulRequests;
    const promptTokens = usage.reduce((s, u) => s + (u.prompt_tokens || 0), 0);
    const completionTokens = usage.reduce((s, u) => s + (u.completion_tokens || 0), 0);
    const totalTokens = promptTokens + completionTokens;
    const totalCost = usage.reduce((s, u) => s + (u.cost_usd || 0), 0);
    
    const successfulUsages = usage.filter((u) => u.status === 'success');
    const avgLatency = successfulUsages.length
      ? successfulUsages.reduce((s, u) => s + (u.latency_ms || 0), 0) / successfulUsages.length
      : 0;

    return {
      totalRequests,
      successfulRequests,
      failedRequests,
      promptTokens,
      completionTokens,
      totalTokens,
      totalCost: parseFloat(totalCost.toFixed(4)),
      avgLatency: Math.round(avgLatency),
    };
  }, [usage]);

  return {
    usage,
    kpis,
    isLoading: query.isLoading,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Analytics
// ─────────────────────────────────────────────────────────────────────────────
export function useAnalytics() {
  const { usage, kpis, isLoading, refetch } = useUsage();

  const charts = React.useMemo(() => {
    if (!usage.length) return { timeSeries: [], providerDist: [], modelDist: [], costTrend: [] };

    // Group by Date for trends
    const dayMap: Record<string, { requests: number; success: number; failure: number; tokens: number; cost: number; latencySum: number; latencyCount: number }> = {};
    const providerMap: Record<string, { tokens: number; cost: number; requests: number }> = {};
    const modelMap: Record<string, { tokens: number; cost: number; requests: number }> = {};

    for (const u of usage) {
      // 1. Time Series grouping
      const dateStr = new Date(u.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      if (!dayMap[dateStr]) {
        dayMap[dateStr] = { requests: 0, success: 0, failure: 0, tokens: 0, cost: 0, latencySum: 0, latencyCount: 0 };
      }
      dayMap[dateStr].requests += 1;
      if (u.status === 'success') {
        dayMap[dateStr].success += 1;
        dayMap[dateStr].latencySum += u.latency_ms || 0;
        dayMap[dateStr].latencyCount += 1;
      } else {
        dayMap[dateStr].failure += 1;
      }
      dayMap[dateStr].tokens += u.total_tokens || 0;
      dayMap[dateStr].cost += u.cost_usd || 0;

      // 2. Provider Distribution grouping
      if (!providerMap[u.provider]) providerMap[u.provider] = { tokens: 0, cost: 0, requests: 0 };
      providerMap[u.provider].tokens += u.total_tokens || 0;
      providerMap[u.provider].cost += u.cost_usd || 0;
      providerMap[u.provider].requests += 1;

      // 3. Model Distribution grouping
      if (!modelMap[u.model_name]) modelMap[u.model_name] = { tokens: 0, cost: 0, requests: 0 };
      modelMap[u.model_name].tokens += u.total_tokens || 0;
      modelMap[u.model_name].cost += u.cost_usd || 0;
      modelMap[u.model_name].requests += 1;
    }

    const timeSeries = Object.entries(dayMap).map(([date, vals]) => ({
      date,
      requests: vals.requests,
      success: vals.success,
      failure: vals.failure,
      tokens: vals.tokens,
      cost: parseFloat(vals.cost.toFixed(6)),
      avgLatency: vals.latencyCount ? Math.round(vals.latencySum / vals.latencyCount) : 0,
    })).reverse().slice(-14).reverse(); // Keep last 14 days sorted chronologically

    const providerDist = Object.entries(providerMap).map(([name, vals]) => ({
      name: PROVIDER_META[name]?.label || name,
      value: vals.requests,
      tokens: vals.tokens,
      cost: parseFloat(vals.cost.toFixed(4)),
    }));

    const modelDist = Object.entries(modelMap).map(([name, vals]) => ({
      name,
      value: vals.requests,
      tokens: vals.tokens,
      cost: parseFloat(vals.cost.toFixed(4)),
    })).sort((a, b) => b.value - a.value).slice(0, 5); // Top 5 models

    return {
      timeSeries,
      providerDist,
      modelDist,
    };
  }, [usage]);

  const performanceBreakdown = React.useMemo(() => {
    const providerPerf: Record<string, { success: number; total: number; latencySum: number; costSum: number }> = {};
    const modelPerf: Record<string, { success: number; total: number; latencySum: number; costSum: number }> = {};

    for (const u of usage) {
      // Provider
      if (!providerPerf[u.provider]) providerPerf[u.provider] = { success: 0, total: 0, latencySum: 0, costSum: 0 };
      providerPerf[u.provider].total += 1;
      providerPerf[u.provider].costSum += u.cost_usd || 0;
      if (u.status === 'success') {
        providerPerf[u.provider].success += 1;
        providerPerf[u.provider].latencySum += u.latency_ms || 0;
      }

      // Model
      if (!modelPerf[u.model_name]) modelPerf[u.model_name] = { success: 0, total: 0, latencySum: 0, costSum: 0 };
      modelPerf[u.model_name].total += 1;
      modelPerf[u.model_name].costSum += u.cost_usd || 0;
      if (u.status === 'success') {
        modelPerf[u.model_name].success += 1;
        modelPerf[u.model_name].latencySum += u.latency_ms || 0;
      }
    }

    const providerList = Object.entries(providerPerf).map(([name, v]) => ({
      name: PROVIDER_META[name]?.label || name,
      requests: v.total,
      successRate: v.total ? Math.round((v.success / v.total) * 100) : 0,
      avgLatency: v.success ? Math.round(v.latencySum / v.success) : 0,
      cost: parseFloat(v.costSum.toFixed(4)),
    }));

    const modelList = Object.entries(modelPerf).map(([name, v]) => ({
      name,
      requests: v.total,
      successRate: v.total ? Math.round((v.success / v.total) * 100) : 0,
      avgLatency: v.success ? Math.round(v.latencySum / v.success) : 0,
      cost: parseFloat(v.costSum.toFixed(4)),
    }));

    return {
      providers: providerList,
      models: modelList,
    };
  }, [usage]);

  return {
    kpis,
    charts,
    performanceBreakdown,
    isLoading,
    refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Routing
// ─────────────────────────────────────────────────────────────────────────────
export function useRouting() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<AIRoutingRule[]>({
    queryKey: ['ai-routing-rules', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/routing-rules/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const createRule = useMutation({
    mutationFn: async (rule: Omit<AIRoutingRule, 'id' | 'organization_id'>) => {
      const res = await apiClient.post('/ai/routing-rules/', rule);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-routing-rules'] });
    },
  });

  const updateRule = useMutation({
    mutationFn: async ({ ruleId, updates }: { ruleId: string; updates: Partial<AIRoutingRule> }) => {
      const res = await apiClient.patch(`/ai/routing-rules/${ruleId}`, updates);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-routing-rules'] });
    },
  });

  const deleteRule = useMutation({
    mutationFn: async (ruleId: string) => {
      await apiClient.delete(`/ai/routing-rules/${ruleId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-routing-rules'] });
    },
  });

  return {
    rules: query.data || [],
    isLoading: query.isLoading,
    refetch: query.refetch,
    createRule,
    updateRule,
    deleteRule,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: ProviderHealth
// ─────────────────────────────────────────────────────────────────────────────
export function useProviderHealth() {
  const queryClient = useQueryClient();

  const testConnection = useMutation({
    mutationFn: async (providerKey: string) => {
      const provsRes = await apiClient.get('/ai/providers/');
      const provList = provsRes.data || [];
      const match = provList.find((p: any) => p.name.toLowerCase() === providerKey.toLowerCase());
      if (!match) {
        throw new Error(`Provider ${providerKey} not found in DB`);
      }
      const res = await apiClient.get(`/ai/providers/${match.id}/health`);
      return res.data;
    },
  });

  const refreshAll = useMutation({
    mutationFn: async () => {
      await queryClient.invalidateQueries({ queryKey: ['ai-models'] });
      await queryClient.invalidateQueries({ queryKey: ['ai-routing-rules'] });
    },
  });

  return {
    testConnection,
    refreshAll,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Latency
// ─────────────────────────────────────────────────────────────────────────────
export function useLatency() {
  const { usage } = useUsage();

  const latencyStats = React.useMemo(() => {
    if (!usage.length) return { avg: 0, p95: 0, breakdown: [] };

    const successUsages = usage.filter((u) => u.status === 'success');
    const latencies = successUsages.map((u) => u.latency_ms || 0).sort((a, b) => a - b);
    const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
    const p95 = latencies[Math.floor(latencies.length * 0.95)] || 0;

    return {
      avg: Math.round(avg),
      p95,
    };
  }, [usage]);

  return latencyStats;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Costs
// ─────────────────────────────────────────────────────────────────────────────
export function useCosts() {
  const { usage } = useUsage();

  const costStats = React.useMemo(() => {
    const totalCost = usage.reduce((s, u) => s + (u.cost_usd || 0), 0);
    const avgCostPerReq = usage.length ? totalCost / usage.length : 0;

    return {
      total: parseFloat(totalCost.toFixed(4)),
      avg: parseFloat(avgCostPerReq.toFixed(6)),
    };
  }, [usage]);

  return costStats;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: ProviderLogs
// ─────────────────────────────────────────────────────────────────────────────
export function useProviderLogs(providerId: string) {
  const { usage, isLoading, refetch } = useUsage();

  const logs = React.useMemo(() => {
    return usage.filter((u) => u.provider.toLowerCase() === providerId.toLowerCase());
  }, [usage, providerId]);

  const stats = React.useMemo(() => {
    if (!logs.length) {
      return {
        totalRequests: 0,
        successRequests: 0,
        failedRequests: 0,
        successRate: 0,
        avgLatency: 0,
        totalCost: 0,
        totalTokens: 0,
        latencyHistory: [],
        incidents: [],
      };
    }

    const totalRequests = logs.length;
    const successRequests = logs.filter((l) => l.status === 'success').length;
    const failedRequests = totalRequests - successRequests;
    const successRate = Math.round((successRequests / totalRequests) * 100);
    
    const successfulLogs = logs.filter((l) => l.status === 'success');
    const avgLatency = successfulLogs.length
      ? successfulLogs.reduce((s, l) => s + (l.latency_ms || 0), 0) / successfulLogs.length
      : 0;

    const totalCost = logs.reduce((s, l) => s + (l.cost_usd || 0), 0);
    const totalTokens = logs.reduce((s, l) => s + (l.total_tokens || 0), 0);

    // Group logs by day to show Health Timeline & Latency
    const dayMap: Record<string, { success: number; total: number; latencySum: number; latencyCount: number }> = {};
    for (const log of logs) {
      const dateStr = new Date(log.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      if (!dayMap[dateStr]) {
        dayMap[dateStr] = { success: 0, total: 0, latencySum: 0, latencyCount: 0 };
      }
      dayMap[dateStr].total += 1;
      if (log.status === 'success') {
        dayMap[dateStr].success += 1;
        dayMap[dateStr].latencySum += log.latency_ms || 0;
        dayMap[dateStr].latencyCount += 1;
      }
    }

    const latencyHistory = Object.entries(dayMap).map(([date, vals]) => ({
      date,
      avgLatency: vals.latencyCount ? Math.round(vals.latencySum / vals.latencyCount) : 0,
      successRate: vals.total ? Math.round((vals.success / vals.total) * 100) : 0,
      requests: vals.total,
    })).reverse().slice(-14).reverse();

    // Map failed requests as incidents
    const incidents = logs
      .filter((l) => l.status === 'failure')
      .map((l) => ({
        id: l.id,
        timestamp: l.created_at,
        modelName: l.model_name,
        error: l.error_message || 'Endpoint connection timeout',
      }))
      .slice(0, 10);

    return {
      totalRequests,
      successRequests,
      failedRequests,
      successRate,
      avgLatency: Math.round(avgLatency),
      totalCost: parseFloat(totalCost.toFixed(4)),
      totalTokens,
      latencyHistory,
      incidents,
    };
  }, [logs]);

  return {
    logs,
    stats,
    isLoading,
    refetch,
  };
}

export interface IncidentLog {
  id: string;
  provider: string;
  timestamp: string;
  type: string;
  message: string;
  resolved: boolean;
}

export function useIncidents() {
  const queryClient = useQueryClient();

  const query = useQuery<IncidentLog[]>({
    queryKey: ['ai-incidents'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers/health/incidents');
      return res.data || [];
    },
  });

  const resolveIncident = useMutation({
    mutationFn: async (incidentId: string) => {
      const res = await apiClient.post(`/ai/providers/health/incidents/${incidentId}/resolve`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-incidents'] });
    },
  });

  return {
    incidents: query.data || [],
    isLoading: query.isLoading,
    refetch: query.refetch,
    resolveIncident,
  };
}

export interface OrgLimitBackend {
  organization_id: string;
  credit_limit: number;
  credit_used: number;
  rpm_limit: number;
  tpm_limit: number;
}

export interface ProviderKeyBackend {
  id: string;
  provider_id: string;
  provider_name: string;
  is_active: boolean;
  masked_key: string;
  created_at: string;
}

export function useAdminConsoleLimits() {
  const queryClient = useQueryClient();

  const orgLimitsQuery = useQuery<OrgLimitBackend[]>({
    queryKey: ['ai-org-limits'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers/limits/orgs');
      return res.data || [];
    },
  });

  const providerKeysQuery = useQuery<ProviderKeyBackend[]>({
    queryKey: ['ai-provider-keys'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers/keys/');
      return res.data || [];
    },
  });

  const addCredits = useMutation({
    mutationFn: async ({ orgId, amount }: { orgId: string; amount: number }) => {
      const res = await apiClient.post(`/ai/providers/limits/${orgId}/credits`, { amount });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-org-limits'] });
    },
  });

  const updateLimits = useMutation({
    mutationFn: async ({ orgId, rpmLimit, tpmLimit }: { orgId: string; rpmLimit: number; tpmLimit: number }) => {
      const res = await apiClient.post(`/ai/providers/limits/${orgId}/limits`, {
        rpm_limit: rpmLimit,
        tpm_limit: tpmLimit,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-org-limits'] });
    },
  });

  const rotateKey = useMutation({
    mutationFn: async ({ providerName, api_key }: { providerName: string; api_key: string }) => {
      const provsRes = await apiClient.get('/ai/providers/');
      const provList = provsRes.data || [];
      const matchProv = provList.find((p: any) => p.name.toLowerCase() === providerName.toLowerCase());
      if (!matchProv) {
        throw new Error(`Provider ${providerName} not found`);
      }

      const keysRes = await apiClient.get('/ai/providers/keys/');
      const existing = (keysRes.data || []).find((k: any) => k.provider_id === matchProv.id);
      
      if (existing) {
        const res = await apiClient.post(`/ai/providers/keys/${existing.id}/rotate`, { api_key });
        return res.data;
      } else {
        const res = await apiClient.post('/ai/providers/keys/', { provider_id: matchProv.id, api_key });
        return res.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-provider-keys'] });
    },
  });

  return {
    orgLimits: orgLimitsQuery.data || [],
    providerKeys: providerKeysQuery.data || [],
    isLoading: orgLimitsQuery.isLoading || providerKeysQuery.isLoading,
    refetch: () => {
      orgLimitsQuery.refetch();
      providerKeysQuery.refetch();
    },
    addCredits,
    updateLimits,
    rotateKey,
  };
}

