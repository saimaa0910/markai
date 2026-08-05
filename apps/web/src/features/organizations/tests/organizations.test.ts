/**
 * @file organizations.test.ts
 * @description Unit tests for Organizations feature.
 */

import { generateOrgSlug } from '../utils/helpers';

describe('Organizations Slug Helper Unit Tests', () => {
  it('should generate valid URL slug from name', () => {
    expect(generateOrgSlug('Acme Corp')).toBe('acme-corp');
  });
});
