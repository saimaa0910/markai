/**
 * @file index.ts
 * @description Enterprise TS Structured Logger.
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export class Logger {
  constructor(private context: string = 'App') {}

  public info(message: string, meta?: Record<string, unknown>): void {
    console.log(`[${new Date().toISOString()}] [INFO] [${this.context}] ${message}`, meta || '');
  }

  public error(message: string, error?: unknown): void {
    console.error(`[${new Date().toISOString()}] [ERROR] [${this.context}] ${message}`, error || '');
  }
}

export const logger = new Logger('EAIMOS');
