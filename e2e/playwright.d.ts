declare module '@playwright/test' {
  export interface PlaywrightTestConfig {
    testDir?: string;
    timeout?: number;
    expect?: {
      timeout?: number;
      [key: string]: any;
    };
    fullyParallel?: boolean;
    forbidOnly?: boolean;
    retries?: number;
    workers?: number | string | undefined;
    reporter?: any[];
    use?: {
      baseURL?: string;
      trace?: string;
      screenshot?: string;
      video?: string;
      [key: string]: any;
    };
    projects?: Array<{
      name: string;
      use?: Record<string, any>;
    }>;
    webServer?: any;
    [key: string]: any;
  }

  export function defineConfig(config: PlaywrightTestConfig): PlaywrightTestConfig;
  export const devices: Record<string, any>;
  export const test: any;
  export const expect: any;
}
