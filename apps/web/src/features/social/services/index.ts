/**
 * Social Studio API Client — Sprint 7.5
 * ========================================
 * All API functions for the Social Media Agent endpoints.
 * Reuses the shared apiClient (auth interceptors, org header, base URL).
 */
import { apiClient } from '../../../services/api-client';
import type {
  SocialGenerateRequest,
  SocialStreamRequest,
  SocialScheduleRequest,
  SocialPublishRequest,
  SocialReplyRequest,
  SocialOptimizeRequest,
  SocialHashtagRequest,
  SocialPostResponse,
  SocialScheduleResponse,
  SocialPublishResponse,
  SocialReplyResponse,
  SocialPlatformInfo,
  SocialHistoryItem,
  SocialTemplate,
  SocialQueueResponse,
  SocialAnalyticsResponse,
  SocialCalendarResponse,
  HashtagResult,
  PlatformOptimizationResult,
} from '../types';

const BASE = '/agents/social';

// ─── Generate ─────────────────────────────────────────────────────────────────

export async function generateSocialPost(
  payload: SocialGenerateRequest
): Promise<SocialPostResponse> {
  const { data } = await apiClient.post<SocialPostResponse>(`${BASE}/generate`, payload);
  return data;
}

// ─── Stream ───────────────────────────────────────────────────────────────────

export function streamSocialPost(
  payload: SocialStreamRequest,
  onEvent: (event: string, data: any) => void,
  onComplete: () => void,
  onError: (err: Error) => void,
  signal?: AbortSignal
): void {
  apiClient
    .post(`${BASE}/stream`, payload, {
      responseType: 'stream',
      signal,
      headers: { Accept: 'text/event-stream' },
    })
    .catch(onError);

  const url = `${apiClient.defaults.baseURL}${BASE}/stream`;
  const eventSource = new EventSource(url);

  const handler = (ev: MessageEvent) => {
    try {
      const parsed = JSON.parse(ev.data);
      onEvent(ev.type, parsed);
    } catch {
      onEvent(ev.type, ev.data);
    }
  };

  const socialEvents = [
    'agent_start', 'planning', 'brand', 'campaign', 'knowledge',
    'content', 'image', 'hashtags', 'optimization', 'reflection',
    'evaluation', 'schedule', 'publish', 'completed', 'llm_token', 'status', 'error',
  ];
  socialEvents.forEach((evt) => eventSource.addEventListener(evt, handler as any));

  eventSource.addEventListener('completed', () => {
    eventSource.close();
    onComplete();
  });

  eventSource.addEventListener('error', (e: any) => {
    eventSource.close();
    onError(new Error('SSE stream error'));
  });
}

// ─── Schedule ─────────────────────────────────────────────────────────────────

export async function schedulePost(
  payload: SocialScheduleRequest
): Promise<SocialScheduleResponse> {
  const { data } = await apiClient.post<SocialScheduleResponse>(`${BASE}/schedule`, payload);
  return data;
}

// ─── Publish ──────────────────────────────────────────────────────────────────

export async function publishPost(
  payload: SocialPublishRequest
): Promise<SocialPublishResponse> {
  const { data } = await apiClient.post<SocialPublishResponse>(`${BASE}/publish`, payload);
  return data;
}

// ─── Reply ────────────────────────────────────────────────────────────────────

export async function generateReply(
  payload: SocialReplyRequest
): Promise<SocialReplyResponse> {
  const { data } = await apiClient.post<SocialReplyResponse>(`${BASE}/reply`, payload);
  return data;
}

// ─── Optimize ─────────────────────────────────────────────────────────────────

export async function optimizeContent(
  payload: SocialOptimizeRequest
): Promise<PlatformOptimizationResult> {
  const { data } = await apiClient.post<PlatformOptimizationResult>(`${BASE}/optimize`, payload);
  return data;
}

// ─── Hashtags ─────────────────────────────────────────────────────────────────

export async function generateHashtags(
  payload: SocialHashtagRequest
): Promise<HashtagResult> {
  const { data } = await apiClient.post<HashtagResult>(`${BASE}/hashtags`, payload);
  return data;
}

// ─── History ──────────────────────────────────────────────────────────────────

export async function fetchSocialHistory(
  limit = 20,
  platform?: string
): Promise<SocialHistoryItem[]> {
  const params: Record<string, any> = { limit };
  if (platform) params.platform = platform;
  const { data } = await apiClient.get<SocialHistoryItem[]>(`${BASE}/history`, { params });
  return data;
}

// ─── Calendar ─────────────────────────────────────────────────────────────────

export async function fetchSocialCalendar(
  view: 'daily' | 'weekly' | 'monthly' = 'weekly'
): Promise<SocialCalendarResponse> {
  const { data } = await apiClient.get<SocialCalendarResponse>(`${BASE}/calendar`, {
    params: { view },
  });
  return data;
}

// ─── Platforms ────────────────────────────────────────────────────────────────

export async function fetchPlatforms(): Promise<SocialPlatformInfo[]> {
  const { data } = await apiClient.get<SocialPlatformInfo[]>(`${BASE}/platforms`);
  return data;
}

// ─── Templates ───────────────────────────────────────────────────────────────

export async function fetchSocialTemplates(): Promise<SocialTemplate[]> {
  const { data } = await apiClient.get<SocialTemplate[]>(`${BASE}/templates`);
  return data;
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export async function fetchSocialAnalytics(
  platform?: string,
  limit = 50
): Promise<SocialAnalyticsResponse> {
  const params: Record<string, any> = { limit };
  if (platform) params.platform = platform;
  const { data } = await apiClient.get<SocialAnalyticsResponse>(`${BASE}/analytics`, { params });
  return data;
}

// ─── Queue ────────────────────────────────────────────────────────────────────

export async function fetchSocialQueue(
  status?: string
): Promise<SocialQueueResponse> {
  const params: Record<string, any> = {};
  if (status) params.status = status;
  const { data } = await apiClient.get<SocialQueueResponse>(`${BASE}/queue`, { params });
  return data;
}
