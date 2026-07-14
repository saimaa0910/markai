'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  change?: string;
  isPositive?: boolean;
  isNeutral?: boolean;
  icon?: React.ReactNode;
  iconColor?: string;
  isLoading?: boolean;
  suffix?: string;
  prefix?: string;
  className?: string;
  onClick?: () => void;
}

export function StatCard({
  title,
  value,
  description,
  change,
  isPositive,
  isNeutral = false,
  icon,
  iconColor = 'text-violet-400',
  isLoading = false,
  suffix,
  prefix,
  className,
  onClick,
}: StatCardProps) {
  const TrendIcon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;
  const trendColor = isNeutral
    ? 'text-neutral-400'
    : isPositive
    ? 'text-emerald-400'
    : 'text-rose-400';

  return (
    <div
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-xl border border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-3 transition-all',
        onClick && 'cursor-pointer hover:border-violet-500/20 hover:bg-neutral-900/40',
        className
      )}
    >
      {/* Top row */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          {title}
        </span>
        {icon && (
          <div className={cn('p-2 rounded-lg bg-neutral-900 border border-white/5', iconColor)}>
            {icon}
          </div>
        )}
      </div>

      {/* Value */}
      {isLoading ? (
        <div className="h-8 w-24 rounded bg-neutral-800 animate-pulse" />
      ) : (
        <div className="flex items-baseline gap-1">
          {prefix && <span className="text-sm text-neutral-400">{prefix}</span>}
          <span className="text-2xl font-extrabold text-white tracking-tight">{value}</span>
          {suffix && <span className="text-sm text-neutral-400">{suffix}</span>}
        </div>
      )}

      {/* Bottom row */}
      <div className="flex items-center justify-between">
        {description && (
          <span className="text-[11px] text-neutral-500 leading-tight">{description}</span>
        )}
        {change && (
          <div className={cn('flex items-center gap-1 text-[11px] font-semibold', trendColor)}>
            <TrendIcon className="w-3 h-3" />
            {change}
          </div>
        )}
      </div>

      {/* Subtle glow accent */}
      <div className="absolute -top-px left-0 right-0 h-px bg-gradient-to-r from-transparent via-violet-500/20 to-transparent" />
    </div>
  );
}
