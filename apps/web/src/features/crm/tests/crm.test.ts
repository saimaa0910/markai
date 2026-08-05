/**
 * @file crm.test.ts
 * @description Unit tests for CRM feature module.
 */

import { formatCurrency } from '../utils';

describe('CRM Utility Unit Tests', () => {
  it('should format currency correctly', () => {
    expect(formatCurrency(1000)).toBe('$1,000.00');
  });
});
