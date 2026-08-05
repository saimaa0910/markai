/**
 * @file helpers.ts
 * @description CRM domain helpers.
 */

export function formatContactName(firstName: string, lastName: string): string {
  return `${firstName} ${lastName}`.trim();
}
