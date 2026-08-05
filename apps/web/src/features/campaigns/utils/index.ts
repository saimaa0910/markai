/**
 * @file index.ts
 * @description Utility functions for Campaigns feature.
 */

export function calculateCampaignRoi(revenue: number, cost: number): number {
  if (cost === 0) return 0;
  return ((revenue - cost) / cost) * 100;
}
