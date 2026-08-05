/**
 * @file feature.test.ts
 * @description Unit tests for AI Platform feature.
 */

import { calculateEstimatedTokenCost } from '../utils';

describe('AI Platform Utilities Unit Tests', () => {
  it('should calculate correct token costs', () => {
    const cost = calculateEstimatedTokenCost(2000, 0.002);
    expect(cost).toBe(0.004);
  });
});
