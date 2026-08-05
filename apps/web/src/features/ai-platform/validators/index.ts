/**
 * @file index.ts
 * @description Custom validators for AI Platform.
 */

export function validateApiKeyFormat(key: string): boolean {
  return key.length >= 10;
}
