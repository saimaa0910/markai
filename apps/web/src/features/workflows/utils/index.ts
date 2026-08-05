/**
 * @file index.ts
 * @description Utility functions for Workflows.
 */

export function generateNodeId(type: string): string {
  return `${type}_${Math.random().toString(36).substring(2, 9)}`;
}
