/**
 * @file campaigns.test.ts
 * @description Unit tests for Campaigns feature module.
 */

import { calculateCampaignRoi } from '../utils';

describe('Campaigns ROI Calculation Unit Tests', () => {
  it('should calculate ROI percentage correctly', () => {
    expect(calculateCampaignRoi(200, 100)).toBe(100);
  });
});
