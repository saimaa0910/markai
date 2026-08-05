/**
 * @file index.ts
 * @description Validators for Campaigns feature.
 */

export function validateCampaignDates(start?: string, end?: string): boolean {
  if (!start || !end) return true;
  return new Date(start) <= new Date(end);
}
