/**
 * @file helpers.ts
 * @description Organization helper utilities.
 */

export function generateOrgSlug(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
}
