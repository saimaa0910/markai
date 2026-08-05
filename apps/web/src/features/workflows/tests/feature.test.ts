/**
 * @file feature.test.ts
 * @description Unit tests for Workflows feature.
 */

import { generateNodeId } from '../utils';

describe('Workflows Utilities Unit Tests', () => {
  it('should generate unique node id with prefix', () => {
    const id = generateNodeId('agent');
    expect(id.startsWith('agent_')).toBe(true);
  });
});
