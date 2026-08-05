/**
 * @file index.ts
 * @description Utility functions for Billing.
 */

export function calculateProratedAmount(amount: number, daysRemaining: number, totalDays: number): number {
  if (totalDays === 0) return 0;
  return (amount * daysRemaining) / totalDays;
}
