/**
 * @file index.ts
 * @description Validators for Workflows feature.
 */

export function validateWorkflowGraph(nodes: unknown[], edges: unknown[]): boolean {
  return nodes.length > 0;
}
