/**
 * @file billing.test.ts
 * @description Unit tests for Billing feature module.
 */

import { calculateProratedAmount } from '../utils';

describe('Billing Proration Unit Tests', () => {
  it('should calculate prorated amount correctly', () => {
    expect(calculateProratedAmount(100, 15, 30)).toBe(50);
  });
});
