/**
 * @file index.ts
 * @description Validators for Billing feature.
 */

export function validateCreditAmount(amount: number): boolean {
  return amount > 0 && Number.isInteger(amount);
}
