/**
 * @file index.ts
 * @description Monorepo Observability Tracing Package.
 */

export function traceSpan<T>(spanName: string, fn: () => Promise<T>): Promise<T> {
  // TODO: Wrap function execution in OpenTelemetry span
  return fn();
}
