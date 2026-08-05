/**
 * @file index.ts
 * @description Validators for CRM feature.
 */

export function validatePhoneNumber(phone: string): boolean {
  const phoneRegex = /^\+?[1-9]\d{1,14}$/;
  return phoneRegex.test(phone);
}
