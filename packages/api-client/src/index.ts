/**
 * @file index.ts
 * @description Isomorphic API Client.
 */

export interface ApiClientConfig {
  baseUrl: string;
  authToken?: string;
}

export class ApiClient {
  constructor(private config: ApiClientConfig) {}

  public async get<T>(endpoint: string): Promise<T> {
    // TODO: Perform fetch GET call
    return {} as T;
  }
}
