/**
 * @file index.ts
 * @description EAIMOS Enterprise SDK Client.
 */

export interface EAIMOSClientOptions {
  apiKey: string;
  baseUrl?: string;
}

export class EAIMOSClient {
  constructor(private options: EAIMOSClientOptions) {}

  public async getStatus(): Promise<{ status: string }> {
    // TODO: Perform handshake call against EAIMOS API
    return { status: 'healthy' };
  }
}
