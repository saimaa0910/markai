/**
 * Agent Feature — Full API Client
 * =================================
 * Sprint 7.1: Complete API client for Agent Runtime Platform.
 * Reuses existing apiClient (auth interceptors, org header, base URL).
 *
 * Covers:
 *  - Agent CRUD
 *  - Sessions
 *  - Runs + Logs
 *  - Chat (single-turn)
 *  - Streaming (SSE)
 *  - Evaluations
 *  - Memory
 *  - Tools list
 */
import { apiClient } from '../../../services/api-client';
import type {
  AgentDefinition,
  AgentSession,
  AgentRun,
  AgentLog,
  AgentMemoryItem,
  AgentEvaluation,
  AgentToolInfo,
  AgentChatRequest,
  AgentStreamRequest,
} from '../types';

const BASE = '/agents';

// ─── Agent Definitions ────────────────────────────────────────────────────────

export async function fetchAgents(): Promise<AgentDefinition[]> {
  const { data } = await apiClient.get(`${BASE}/definitions`);
  return data.items ?? data;
}

export async function fetchAgent(agentId: string): Promise<AgentDefinition> {
  const { data } = await apiClient.get(`${BASE}/definitions/${agentId}`);
  return data;
}

export async function createAgent(payload: Partial<AgentDefinition>): Promise<AgentDefinition> {
  const { data } = await apiClient.post(`${BASE}/definitions`, payload);
  return data;
}

export async function updateAgent(agentId: string, payload: Partial<AgentDefinition>): Promise<AgentDefinition> {
  const { data } = await apiClient.patch(`${BASE}/definitions/${agentId}`, payload);
  return data;
}

export async function deleteAgent(agentId: string): Promise<void> {
  await apiClient.delete(`${BASE}/definitions/${agentId}`);
}

export async function fetchAgentTemplates(): Promise<any[]> {
  const { data } = await apiClient.get(`${BASE}/templates`);
  return data;
}

export async function toggleFavoriteAgent(agentId: string): Promise<AgentDefinition> {
  const { data } = await apiClient.patch(`${BASE}/definitions/${agentId}/favorite`);
  return data;
}

export async function fetchAgentAnalytics(agentId: string): Promise<any> {
  const { data } = await apiClient.get(`${BASE}/definitions/${agentId}/analytics`);
  return data;
}

// ─── Sessions ─────────────────────────────────────────────────────────────────

export async function fetchSessions(): Promise<AgentSession[]> {
  const { data } = await apiClient.get(`${BASE}/sessions`);
  return data.items ?? data;
}

export async function fetchSession(sessionId: string): Promise<AgentSession> {
  const { data } = await apiClient.get(`${BASE}/sessions/${sessionId}`);
  return data;
}

export async function createSession(agentId: string, title: string): Promise<AgentSession> {
  const { data } = await apiClient.post(`${BASE}/sessions`, { agent_id: agentId, title });
  return data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete(`${BASE}/sessions/${sessionId}`);
}

// ─── Runs ──────────────────────────────────────────────────────────────────────

export async function runAgentSession(sessionId: string, userInput: string): Promise<AgentRun> {
  const { data } = await apiClient.post(`${BASE}/sessions/${sessionId}/run`, { user_input: userInput });
  return data;
}

export async function fetchRuns(sessionId: string): Promise<AgentRun[]> {
  const { data } = await apiClient.get(`${BASE}/sessions/${sessionId}/runs`);
  return data.items ?? data;
}

export async function fetchRunLogs(runId: string): Promise<AgentLog[]> {
  const { data } = await apiClient.get(`${BASE}/runs/${runId}/logs`);
  return data;
}

// ─── Sprint 7.1 — Runtime ─────────────────────────────────────────────────────

/** Single-turn chat: creates a session + run in one call. */
export async function chatAgent(agentId: string, req: AgentChatRequest): Promise<AgentRun> {
  const { data } = await apiClient.post(`${BASE}/definitions/${agentId}/chat`, req);
  return data;
}

/**
 * SSE streaming: returns an EventSource connected to the streaming endpoint.
 * The caller is responsible for attaching event listeners and closing the stream.
 *
 * Usage:
 *   const es = streamAgent(agentId, req);
 *   es.addEventListener('token', (e) => console.log(JSON.parse(e.data)));
 *   es.addEventListener('done', () => es.close());
 */
export function streamAgentSSE(agentId: string, req: AgentStreamRequest): EventSource {
  // For SSE with POST body we use a fetch-based approach via a pre-created URL.
  // Since EventSource only supports GET, we need to create a unique stream token
  // or use a custom SSE fetch implementation.
  // Implementation: POST to create a stream token, then GET with token via EventSource.
  // For simplicity in this sprint, we pass the params via query string for GET,
  // or use a manual fetch stream approach below.
  throw new Error('Use streamAgentFetch() for POST-body SSE streaming.');
}

/**
 * Fetch-based SSE streaming for POST body support.
 * Returns an async generator that yields parsed SSE events.
 */
export async function* streamAgentFetch(
  agentId: string,
  req: AgentStreamRequest,
  getToken: () => string | null,
  getOrgId: () => string | null,
): AsyncGenerator<{ event: string; data: any }> {
  const API_BASE = apiClient.defaults.baseURL || '/api/v1';

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  };

  const token = getToken();
  const orgId = getOrgId();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (orgId) headers['X-Organization-ID'] = orgId;

  const response = await fetch(`${API_BASE}${BASE}/definitions/${agentId}/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    throw new Error(`Stream request failed: ${response.status} ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body reader available');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() ?? '';

    for (const block of lines) {
      if (!block.trim()) continue;
      let eventType = 'message';
      let dataStr = '';

      for (const line of block.split('\n')) {
        if (line.startsWith('event: ')) eventType = line.slice(7).trim();
        if (line.startsWith('data: ')) dataStr = line.slice(6).trim();
      }

      try {
        yield { event: eventType, data: JSON.parse(dataStr) };
      } catch {
        yield { event: eventType, data: dataStr };
      }
    }
  }
}

// ─── Evaluations ──────────────────────────────────────────────────────────────

export async function fetchEvaluations(agentId: string, limit = 20): Promise<AgentEvaluation[]> {
  const { data } = await apiClient.get(`${BASE}/definitions/${agentId}/evaluations`, {
    params: { limit },
  });
  return data;
}

// ─── Memory ───────────────────────────────────────────────────────────────────

export async function fetchSessionMemory(sessionId: string, limit = 20): Promise<AgentMemoryItem[]> {
  const { data } = await apiClient.get(`${BASE}/sessions/${sessionId}/memory`, {
    params: { limit },
  });
  return data;
}

export async function writeSessionMemory(
  sessionId: string,
  key: string,
  value: string,
  importance = 0.5,
): Promise<AgentMemoryItem> {
  const { data } = await apiClient.post(
    `${BASE}/sessions/${sessionId}/memory`,
    null,
    { params: { key, value, importance } },
  );
  return data;
}

// ─── Tools ────────────────────────────────────────────────────────────────────

export async function fetchTools(): Promise<AgentToolInfo[]> {
  const { data } = await apiClient.get(`${BASE}/tools`);
  return data;
}

/** @deprecated Use individual named exports. Kept for backward compat. */
export async function fetchAgentConfigs(): Promise<AgentDefinition[]> {
  return fetchAgents();
}
