/**
 * @file index.ts
 * @description Feature Flag Evaluation Engine.
 */

export class FeatureFlagService {
  private flags: Map<string, boolean> = new Map();

  public isEnabled(flagName: string): boolean {
    return this.flags.get(flagName) ?? false;
  }

  public setFlag(flagName: string, enabled: boolean): void {
    this.flags.set(flagName, enabled);
  }
}

export const featureFlags = new FeatureFlagService();
