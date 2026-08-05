/**
 * @file seo.test.ts
 * @description Unit tests for SEO feature module.
 */

import { calculateKeywordDifficultyCategory } from '../utils';

describe('SEO Difficulty Category Unit Tests', () => {
  it('should categorize difficulty scores correctly', () => {
    expect(calculateKeywordDifficultyCategory(25)).toBe('Easy');
    expect(calculateKeywordDifficultyCategory(50)).toBe('Medium');
    expect(calculateKeywordDifficultyCategory(80)).toBe('Hard');
  });
});
