import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';

export interface TraceRecord {
  id: string;
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  name: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  status: string;
  error_message: string | null;
  attributes: Record<string, any> | null;
}

export interface LogRecord {
  id: string;
  trace_id: string | null;
  span_id: string | null;
  correlation_id: string | null;
  request_id: string | null;
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  payload: Record<string, any> | null;
}

export interface IncidentRecord {
  id: string;
  component: string;
  service: string;
  severity: string;
  root_cause: string;
  resolution: string | null;
  status: string;
  start_time: string;
  end_time: string | null;
  duration_sec: number | null;
}

export interface AlertRecord {
  id: string;
  incident_id: string | null;
  alert_type: string;
  message: string;
  severity: string;
  channels: string;
  status: string;
  created_at: string;
}

export interface PerformanceAnalytics {
  summary: {
    total_traces: number;
    average_ms: number;
    p50_ms: number;
    p90_ms: number;
    p95_ms: number;
    p99_ms: number;
    max_ms: number;
    min_ms: number;
  };
  provider_comparison: Array<{
    provider: string;
    model: string;
    avg_latency_ms: number;
    requests_count: number;
    total_cost_usd: number;
  }>;
  cache_performance: {
    hits: number;
    misses: number;
    hit_ratio: number;
  };
}

export interface SystemHealth {
  success: boolean;
  status: string;
  timestamp: string;
  components: Record<string, string>;
  details: Record<string, any>;
}

export interface LiveObservabilitySnapshot {
  timestamp: string;
  traffic_5m: {
    requests_count: number;
    errors_count: number;
    avg_latency_ms: number;
    throughput_rpm: number;
  };
  redis: {
    status: string;
    used_memory: string;
    connections: number;
  };
  workers: {
    active_workers_count: number;
    jobs_total: number;
    jobs_running: number;
  };
  queues: Record<string, any>;
  active_incidents: Array<{
    id: string;
    component: string;
    service: string;
    severity: string;
    root_cause: string;
    start_time: string;
  }>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks Definition
// ─────────────────────────────────────────────────────────────────────────────

export function useObservabilityHealth() {
  return useQuery<SystemHealth>({
    queryKey: ['observability-health'],
    queryFn: async () => {
      const res = await apiClient.get('/observability/health');
      return res.data;
    },
    refetchInterval: 10000, // Refresh health status every 10s
  });
}

export function useObservabilityTraces(filters: { trace_id?: string; name?: string; status?: string } = {}) {
  return useQuery<TraceRecord[]>({
    queryKey: ['observability-traces', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.trace_id) params.append('trace_id', filters.trace_id);
      if (filters.name) params.append('name', filters.name);
      if (filters.status) params.append('status', filters.status);
      
      const res = await apiClient.get(`/observability/traces?${params.toString()}`);
      return res.data || [];
    },
  });
}

export function useObservabilityLogs(filters: { search?: string; level?: string; trace_id?: string } = {}) {
  return useQuery<LogRecord[]>({
    queryKey: ['observability-logs', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.level && filters.level !== 'ALL') params.append('level', filters.level);
      if (filters.trace_id) params.append('trace_id', filters.trace_id);
      
      const res = await apiClient.get(`/observability/logs?${params.toString()}`);
      return res.data || [];
    },
  });
}

export function useObservabilityIncidents(status?: string) {
  return useQuery<IncidentRecord[]>({
    queryKey: ['observability-incidents', status],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      
      const res = await apiClient.get(`/observability/incidents?${params.toString()}`);
      return res.data || [];
    },
  });
}

export function useObservabilityAlerts() {
  return useQuery<AlertRecord[]>({
    queryKey: ['observability-alerts'],
    queryFn: async () => {
      const res = await apiClient.get('/observability/alerts');
      return res.data || [];
    },
  });
}

export function useObservabilityPerformance(days: number = 7) {
  return useQuery<PerformanceAnalytics>({
    queryKey: ['observability-performance', days],
    queryFn: async () => {
      const res = await apiClient.get(`/observability/performance?days=${days}`);
      return res.data;
    },
  });
}

export function useObservabilityLive() {
  return useQuery<LiveObservabilitySnapshot>({
    queryKey: ['observability-live'],
    queryFn: async () => {
      const res = await apiClient.get('/observability/live');
      return res.data;
    },
    refetchInterval: 3000, // Fetch live updates every 3s
  });
}

export function useTestAlertMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (severity: string = 'warning') => {
      const res = await apiClient.post(`/observability/alerts/test?severity=${severity}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['observability-alerts'] });
    },
  });
}
