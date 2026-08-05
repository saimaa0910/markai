/**
 * @file feature.test.ts
 * @description Unit tests for Agents feature.
 */

import { validateAgentName } from '../validators';

describe('Agents Feature Validation Unit Tests', () => {
  it('should validate non-empty agent name', () => {
    expect(validateAgentName('Copywriter Agent')).toBe(true);
    expect(validateAgentName('   ')).toBe(false);
  });
});
