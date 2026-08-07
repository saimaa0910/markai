/**
 * Content Studio API Client — Sprint 7.2
 */
import { apiClient } from '../../../services/api-client';
import type {
  ContentGenerateRequest,
  ContentImproveRequest,
  ContentResponse,
  ContentTemplate,
  ContentHistoryItem,
  ContentSEOMetrics,
} from '../types';

const BASE = '/agents/content';

const getAuthToken = (): string | null => {
  try {
    const s = localStorage.getItem('eaimos-auth-storage');
    return s ? JSON.parse(s)?.state?.accessToken ?? null : null;
  } catch { return null; }
};

const getOrgId = (): string | null => {
  try {
    const s = localStorage.getItem('eaimos-auth-storage');
    return s ? JSON.parse(s)?.state?.activeOrg?.id ?? null : null;
  } catch { return null; }
};

export async function generateContent(req: ContentGenerateRequest): Promise<ContentResponse> {
  const { data } = await apiClient.post(`${BASE}/generate`, req);
  return data;
}

export async function improveContent(req: ContentImproveRequest): Promise<{ improved_content: string }> {
  const { data } = await apiClient.post(`${BASE}/improve`, req);
  return data;
}

export async function fetchTemplates(): Promise<ContentTemplate[]> {
  const { data } = await apiClient.get(`${BASE}/templates`);
  return data;
}

export async function fetchHistory(): Promise<ContentHistoryItem[]> {
  const { data } = await apiClient.get(`${BASE}/history`);
  return data;
}

export async function fetchSEOMetrics(content: string, keywords: string[]): Promise<ContentSEOMetrics> {
  const { data } = await apiClient.post(`${BASE}/seo`, null, {
    params: {
      content,
      keywords: keywords.join(','),
    },
  });
  return data;
}

/**
 * Fetch-based SSE generator supporting POST body payloads for content generation.
 */
export async function* streamContentFetch(
  req: ContentGenerateRequest
): AsyncGenerator<{ event: string; data: any }> {
  const API_BASE = apiClient.defaults.baseURL || '/api/v1';

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  };

  const token = getAuthToken();
  const orgId = getOrgId();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (orgId) headers['X-Organization-ID'] = orgId;

  const response = await fetch(`${API_BASE}${BASE}/stream`, {
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
