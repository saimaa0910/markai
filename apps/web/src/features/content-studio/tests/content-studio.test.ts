/**
 * @file content-studio.test.ts
 * @description Unit tests for Content Studio feature.
 */

import { estimateReadTimeMinutes } from '../utils';

describe('Content Studio Read Time Unit Tests', () => {
  it('should estimate reading time correctly', () => {
    const text = Array(400).fill('word').join(' ');
    expect(estimateReadTimeMinutes(text)).toBe(2);
  });
});
