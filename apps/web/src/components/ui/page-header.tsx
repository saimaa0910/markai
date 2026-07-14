'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';

export interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  icon,
  actions,
  badge,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        'flex flex-col sm:flex-row sm:items-center justify-between gap-4',
        className
      )}
    >
      <div className="flex items-start gap-3">
        {icon && (
          <div className="mt-0.5 p-2.5 rounded-xl bg-violet-600/10 border border-violet-500/20 text-violet-400 shrink-0">
            {icon}
          </div>
        )}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-extrabold tracking-tight text-white">{title}</h1>
            {badge}
          </div>
          {description && (
            <p className="text-sm text-neutral-400 leading-relaxed max-w-2xl">{description}</p>
          )}
        </div>
      </div>

      {actions && (
        <div className="flex items-center gap-2 shrink-0 self-start sm:self-auto">
          {actions}
        </div>
      )}
    </header>
  );
}
