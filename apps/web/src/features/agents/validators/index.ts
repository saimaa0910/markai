/**
 * @file index.ts
 * @description Custom validators for Agents feature.
 */

export function validateAgentName(name: string): boolean {
  return name.trim().length > 0;
}
