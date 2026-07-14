'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';
import { Button } from './button';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'violet' | 'outline' | 'secondary';
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
  compact?: boolean;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center',
        compact ? 'py-8 gap-3' : 'py-16 gap-4',
        className
      )}
    >
      {icon && (
        <div
          className={cn(
            'rounded-2xl bg-neutral-900 border border-white/5 text-neutral-600 flex items-center justify-center',
            compact ? 'w-12 h-12' : 'w-16 h-16'
          )}
        >
          {icon}
        </div>
      )}

      <div className="flex flex-col gap-1 max-w-xs">
        <h3
          className={cn(
            'font-bold text-white',
            compact ? 'text-sm' : 'text-base'
          )}
        >
          {title}
        </h3>
        {description && (
          <p className="text-[12px] text-neutral-500 leading-relaxed">{description}</p>
        )}
      </div>

      {(action || secondaryAction) && (
        <div className="flex items-center gap-2 mt-1">
          {action && (
            <Button
              variant={action.variant ?? 'violet'}
              size="sm"
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button variant="ghost" size="sm" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
