'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';

export type BadgeVariant =
  | 'default'
  | 'violet'
  | 'emerald'
  | 'rose'
  | 'amber'
  | 'sky'
  | 'neutral'
  | 'outline';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  default:  'bg-neutral-800 text-neutral-300 border-white/10',
  violet:   'bg-violet-500/10 text-violet-400 border-violet-500/20',
  emerald:  'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  rose:     'bg-rose-500/10 text-rose-400 border-rose-500/20',
  amber:    'bg-amber-500/10 text-amber-400 border-amber-500/20',
  sky:      'bg-sky-500/10 text-sky-400 border-sky-500/20',
  neutral:  'bg-neutral-800/60 text-neutral-400 border-white/5',
  outline:  'bg-transparent text-neutral-400 border-white/15',
};

const dotColors: Record<BadgeVariant, string> = {
  default:  'bg-neutral-400',
  violet:   'bg-violet-400',
  emerald:  'bg-emerald-400',
  rose:     'bg-rose-400',
  amber:    'bg-amber-400',
  sky:      'bg-sky-400',
  neutral:  'bg-neutral-500',
  outline:  'bg-neutral-400',
};

export function Badge({
  variant = 'default',
  size = 'md',
  dot = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-semibold uppercase tracking-wide border rounded-full',
        size === 'sm' ? 'text-[9px] px-1.5 py-0.5' : 'text-[10px] px-2 py-0.5',
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColors[variant])}
        />
      )}
      {children}
    </span>
  );
}

