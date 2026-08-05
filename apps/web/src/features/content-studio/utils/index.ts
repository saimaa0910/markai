/**
 * @file index.ts
 * @description Utility functions for Content Studio.
 */

export function estimateReadTimeMinutes(text: string, wordsPerMinute: number = 200): number {
  const wordCount = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.ceil(wordCount / wordsPerMinute);
}
