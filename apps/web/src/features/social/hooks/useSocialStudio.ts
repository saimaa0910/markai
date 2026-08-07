/**
 * Social Studio Hook — Sprint 7.5
 * =================================
 * React Query hooks for queries and mutations.
 * Follows the same pattern as useImageStudio.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useRef, useCallback } from 'react';
import {
  generateSocialPost,
  schedulePost,
  publishPost,
  generateReply,
  optimizeContent,
  generateHashtags,
  fetchSocialHistory,
  fetchSocialCalendar,
  fetchPlatforms,
  fetchSocialTemplates,
  fetchSocialAnalytics,
  fetchSocialQueue,
} from '../services';
import type {
  SocialGenerateRequest,
  SocialStreamRequest,
  SocialScheduleRequest,
  SocialPublishRequest,
  SocialReplyRequest,
  SocialOptimizeRequest,
  SocialHashtagRequest,
  SocialPostResponse,
  SocialStreamEventType,
} from '../types';
import { apiClient } from '../../../services/api-client';
import { useAuthStore } from '@/store/auth';

const QUERY_KEYS = {
  history: (platform?: string) => ['social', 'history', platform],
  calendar: (view: string) => ['social', 'calendar', view],
  platforms: () => ['social', 'platforms'],
  templates: () => ['social', 'templates'],
  analytics: (platform?: string) => ['social', 'analytics', platform],
  queue: (status?: string) => ['social', 'queue', status],
};

export const useSocialStudio = () => {
  const queryClient = useQueryClient();
  const { accessToken, activeOrg } = useAuthStore();

  // ─── Queries ────────────────────────────────────────────────────────────────

  const useHistory = (platform?: string) =>
    useQuery({
      queryKey: QUERY_KEYS.history(platform),
      queryFn: () => fetchSocialHistory(20, platform),
    });

  const useCalendar = (view: 'daily' | 'weekly' | 'monthly' = 'weekly') =>
    useQuery({
      queryKey: QUERY_KEYS.calendar(view),
      queryFn: () => fetchSocialCalendar(view),
    });

  const usePlatforms = () =>
    useQuery({
      queryKey: QUERY_KEYS.platforms(),
      queryFn: fetchPlatforms,
      staleTime: 5 * 60 * 1000,
    });

  const useTemplates = () =>
    useQuery({
      queryKey: QUERY_KEYS.templates(),
      queryFn: fetchSocialTemplates,
      staleTime: 10 * 60 * 1000,
    });

  const useAnalytics = (platform?: string) =>
    useQuery({
      queryKey: QUERY_KEYS.analytics(platform),
      queryFn: () => fetchSocialAnalytics(platform),
    });

  const useQueue = (status?: string) =>
    useQuery({
      queryKey: QUERY_KEYS.queue(status),
      queryFn: () => fetchSocialQueue(status),
    });

  // ─── Mutations ──────────────────────────────────────────────────────────────

  const generateMutation = useMutation<SocialPostResponse, Error, SocialGenerateRequest>({
    mutationFn: generateSocialPost,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['social', 'queue'] });
    },
  });

  const scheduleMutation = useMutation({
    mutationFn: (payload: SocialScheduleRequest) => schedulePost(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social', 'queue'] });
      queryClient.invalidateQueries({ queryKey: ['social', 'calendar'] });
    },
  });

  const publishMutation = useMutation({
    mutationFn: (payload: SocialPublishRequest) => publishPost(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['social', 'queue'] });
    },
  });

  const replyMutation = useMutation({
    mutationFn: (payload: SocialReplyRequest) => generateReply(payload),
  });

  const optimizeMutation = useMutation({
    mutationFn: (payload: SocialOptimizeRequest) => optimizeContent(payload),
  });

  const hashtagsMutation = useMutation({
    mutationFn: (payload: SocialHashtagRequest) => generateHashtags(payload),
  });

  // ─── SSE Streaming ──────────────────────────────────────────────────────────

  const [streamTokens, setStreamTokens] = useState('');
  const [streamEvents, setStreamEvents] = useState<Array<{ type: SocialStreamEventType; data: any }>>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamResult, setStreamResult] = useState<SocialPostResponse | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const startStream = useCallback(
    async (payload: SocialStreamRequest) => {
      // Cancel any active stream
      if (abortRef.current) abortRef.current.abort();
      abortRef.current = new AbortController();

      setStreamTokens('');
      setStreamEvents([]);
      setStreamResult(null);
      setIsStreaming(true);

      try {
        const apiBase = apiClient.defaults.baseURL || '/api/v1';
        const response = await fetch(
          `${apiBase}/agents/social/stream`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${accessToken || ''}`,
              'X-Organization-ID': activeOrg?.id || '',
            },
            body: JSON.stringify(payload),
            signal: abortRef.current.signal,
          }
        );

        if (!response.ok) throw new Error(`Stream error: ${response.status}`);
        if (!response.body) throw new Error('No response body');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';

          for (const part of parts) {
            if (!part.trim()) continue;
            const eventMatch = part.match(/^event: (.+)/m);
            const dataMatch = part.match(/^data: (.+)/m);
            if (!dataMatch) continue;

            const eventType = (eventMatch?.[1]?.trim() || 'message') as SocialStreamEventType;
            let data: any;
            try {
              data = JSON.parse(dataMatch[1]);
            } catch {
              data = dataMatch[1];
            }

            setStreamEvents((prev) => [...prev, { type: eventType, data }]);

            if (eventType === 'llm_token') {
              setStreamTokens((prev) => prev + (data?.token || ''));
            }
            if (eventType === 'completed') {
              setStreamResult(data as SocialPostResponse);
              queryClient.invalidateQueries({ queryKey: ['social', 'history'] });
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          console.error('Social SSE stream failed:', err);
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [queryClient]
  );

  const stopStream = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return {
    // Queries
    useHistory,
    useCalendar,
    usePlatforms,
    useTemplates,
    useAnalytics,
    useQueue,
    // Mutations
    generateMutation,
    scheduleMutation,
    publishMutation,
    replyMutation,
    optimizeMutation,
    hashtagsMutation,
    // Streaming
    startStream,
    stopStream,
    streamTokens,
    streamEvents,
    isStreaming,
    streamResult,
  };
};

export default useSocialStudio;
