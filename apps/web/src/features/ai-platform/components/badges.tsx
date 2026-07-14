import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import { Zap, DollarSign, Activity, AlertCircle } from 'lucide-react';

interface LatencyBadgeProps {
  latencyMs: number;
}

export function LatencyBadge({ latencyMs }: LatencyBadgeProps) {
  let variant: 'emerald' | 'amber' | 'rose' = 'emerald';
  if (latencyMs > 1000) {
    variant = 'rose';
  } else if (latencyMs > 300) {
    variant = 'amber';
  }

  return (
    <Badge variant={variant} className="gap-1 font-mono text-[11px]" size="sm">
      <Zap className="w-3 h-3 shrink-0 text-current" />
      {latencyMs}ms
    </Badge>
  );
}

interface CostBadgeProps {
  cost: number;
  perMillion?: boolean;
}

export function CostBadge({ cost, perMillion = false }: CostBadgeProps) {
  const formattedCost = cost.toFixed(perMillion ? 2 : 4);
  return (
    <Badge variant="neutral" className="gap-1 font-mono text-[11px]" size="sm">
      <DollarSign className="w-3 h-3 shrink-0 text-neutral-400" />
      ${formattedCost}
      <span className="text-neutral-500 font-normal">{perMillion ? '/1M' : '/1k'}</span>
    </Badge>
  );
}

interface HealthBadgeProps {
  isHealthy: boolean;
  statusLabel?: string;
}

export function HealthBadge({ isHealthy, statusLabel }: HealthBadgeProps) {
  return (
    <Badge variant={isHealthy ? 'emerald' : 'rose'} dot size="sm">
      {statusLabel || (isHealthy ? 'Healthy' : 'Failing')}
    </Badge>
  );
}
