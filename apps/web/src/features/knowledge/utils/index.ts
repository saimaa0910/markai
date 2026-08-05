/**
 * @file index.ts
 * @description Utility functions for Knowledge Base feature.
 */

export function truncateDocSummary(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}
