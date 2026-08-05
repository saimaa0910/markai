/**
 * @file index.ts
 * @description Utility functions for SEO.
 */

export function calculateKeywordDifficultyCategory(difficultyScore: number): 'Easy' | 'Medium' | 'Hard' {
  if (difficultyScore < 30) return 'Easy';
  if (difficultyScore < 70) return 'Medium';
  return 'Hard';
}
