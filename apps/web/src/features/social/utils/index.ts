/**
 * Social Studio Utilities — Sprint 7.5
 */
import type { SocialPlatform, SocialContentType } from '../types';

// ─── Platform Icons ───────────────────────────────────────────────────────────

export const PLATFORM_ICONS: Record<SocialPlatform, string> = {
  LINKEDIN: '💼',
  TWITTER: '🐦',
  FACEBOOK: '📘',
  INSTAGRAM: '📸',
  THREADS: '🧵',
  PINTEREST: '📌',
  TIKTOK: '🎵',
  YOUTUBE_COMMUNITY: '▶️',
  YOUTUBE_SHORTS: '📹',
  REDDIT: '🤖',
  DISCORD: '💬',
  TELEGRAM: '✈️',
  MEDIUM: '📝',
  QUORA: '❓',
};

export const PLATFORM_COLORS: Record<SocialPlatform, string> = {
  LINKEDIN: '#0A66C2',
  TWITTER: '#1DA1F2',
  FACEBOOK: '#1877F2',
  INSTAGRAM: '#E4405F',
  THREADS: '#000000',
  PINTEREST: '#E60023',
  TIKTOK: '#010101',
  YOUTUBE_COMMUNITY: '#FF0000',
  YOUTUBE_SHORTS: '#FF0000',
  REDDIT: '#FF4500',
  DISCORD: '#5865F2',
  TELEGRAM: '#26A5E4',
  MEDIUM: '#000000',
  QUORA: '#A82400',
};

export const CONTENT_TYPE_ICONS: Record<SocialContentType, string> = {
  POST: '📋',
  THREAD: '🧵',
  CAROUSEL: '🎠',
  STORY: '⭕',
  REEL: '🎬',
  SHORT: '⚡',
  ANNOUNCEMENT: '📢',
  LAUNCH_POST: '🚀',
  CASE_STUDY: '📊',
  TESTIMONIAL: '💬',
  POLL: '📊',
  QUESTION: '❓',
  MEME: '😄',
  EDUCATIONAL: '🎓',
  PRODUCT_UPDATE: '🔧',
  HIRING_POST: '👥',
  COMMUNITY_POST: '🤝',
  NEWSLETTER_PROMO: '📩',
  EVENT_PROMO: '🎪',
  BLOG_PROMO: '✍️',
};

// ─── Format helpers ───────────────────────────────────────────────────────────

export function formatPlatformName(platform: string): string {
  return platform.replace(/_/g, ' ').split(' ').map(w => w[0] + w.slice(1).toLowerCase()).join(' ');
}

export function formatContentTypeName(ct: string): string {
  return ct.replace(/_/g, ' ').split(' ').map(w => w[0] + w.slice(1).toLowerCase()).join(' ');
}

export function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function getScoreColor(score: number): string {
  if (score >= 0.8) return '#10b981'; // green
  if (score >= 0.6) return '#f59e0b'; // amber
  return '#ef4444'; // red
}

export function truncateText(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 3) + '...';
}

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

export function copyToClipboard(text: string): Promise<void> {
  return navigator.clipboard.writeText(text);
}
