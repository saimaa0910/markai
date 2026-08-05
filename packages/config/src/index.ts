/**
 * @file index.ts
 * @description Monorepo Shared Configuration Package.
 */

export interface SharedAppConfig {
  appName: string;
  environment: 'development' | 'staging' | 'production';
  version: string;
}

export const sharedConfig: SharedAppConfig = {
  appName: 'EAIMOS',
  environment: (process.env.NODE_ENV as 'development' | 'staging' | 'production') || 'development',
  version: '1.0.0',
};
