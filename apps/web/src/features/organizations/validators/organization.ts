/**
 * @file organization.ts
 * @description Organization validators.
 */

export function validateOrgSlugFormat(slug: string): boolean {
  return /^[a-z0-9-]+$/.test(slug);
}
