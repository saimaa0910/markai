/**
 * @file index.ts
 * @description Frontend Runtime Configuration.
 */

export interface AppConfig {
  apiUrl: string;
  enableAnalytics: boolean;
  maxFileUploadSizeMB: number;
}

export const config: AppConfig = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
  maxFileUploadSizeMB: 50,
};
