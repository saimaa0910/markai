/**
 * @file index.ts
 * @description AI Platform utilities.
 */

export function calculateEstimatedTokenCost(tokens: number, costPerThousand: number): number {
  return (tokens / 1000) * costPerThousand;
}
