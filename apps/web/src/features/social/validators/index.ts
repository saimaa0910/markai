/**
 * Social Studio Validators — Sprint 7.5
 */
import type { SocialPlatform } from '../types';

const PLATFORM_CHAR_LIMITS: Record<string, number> = {
  LINKEDIN: 3000,
  TWITTER: 280,
  FACEBOOK: 63206,
  INSTAGRAM: 2200,
  THREADS: 500,
  PINTEREST: 500,
  TIKTOK: 2200,
  YOUTUBE_COMMUNITY: 5000,
  YOUTUBE_SHORTS: 5000,
  REDDIT: 40000,
  DISCORD: 2000,
  TELEGRAM: 4096,
  MEDIUM: 100000,
  QUORA: 10000,
};

export function validatePrompt(prompt: string): string | null {
  if (!prompt.trim()) return 'Prompt is required.';
  if (prompt.length < 10) return 'Prompt must be at least 10 characters.';
  if (prompt.length > 5000) return 'Prompt cannot exceed 5000 characters.';
  return null;
}

export function validatePlatformContent(content: string, platform: SocialPlatform): string | null {
  const limit = PLATFORM_CHAR_LIMITS[platform];
  if (limit && content.length > limit) {
    return `Content exceeds ${platform} limit of ${limit} characters (currently ${content.length}).`;
  }
  return null;
}

export function validateScheduleDate(scheduledAt: string): string | null {
  const date = new Date(scheduledAt);
  if (isNaN(date.getTime())) return 'Invalid date format.';
  if (date < new Date()) return 'Scheduled date cannot be in the past.';
  return null;
}

export function getCharCount(content: string, platform: SocialPlatform): {
  used: number;
  limit: number;
  remaining: number;
  percentage: number;
  status: 'ok' | 'warning' | 'danger';
} {
  const limit = PLATFORM_CHAR_LIMITS[platform] ?? 2200;
  const used = content.length;
  const remaining = limit - used;
  const percentage = (used / limit) * 100;
  const status = percentage > 95 ? 'danger' : percentage > 80 ? 'warning' : 'ok';
  return { used, limit, remaining, percentage, status };
}
