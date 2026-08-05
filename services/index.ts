/**
 * @file index.ts
 * @description Root entry point for Enterprise Microservices Registry.
 */

export interface ServiceConfig {
  name: string;
  version: string;
  enabled: boolean;
  endpoint?: string;
}

export interface ServiceHealthStatus {
  status: 'healthy' | 'degraded' | 'down';
  uptimeSeconds: number;
  lastChecked: string;
}

/**
 * Enterprise Service Registry Base Class
 */
export class ServiceRegistry {
  private services: Map<string, ServiceConfig> = new Map();

  /**
   * Register a new service definition
   */
  public registerService(config: ServiceConfig): void {
    // TODO: Validate service configuration and register health checks
    this.services.set(config.name, config);
  }

  /**
   * Retrieve registered service config
   */
  public getService(name: string): ServiceConfig | undefined {
    return this.services.get(name);
  }
}

export const defaultServiceRegistry = new ServiceRegistry();
