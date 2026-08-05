'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';
import { Bot, User, Cpu, Activity, Play, AlertCircle, CheckCircle2 } from 'lucide-react';
import { AgentStatus, AgentRunStatus } from '../types';

interface AgentAvatarProps {
  name: string;
  avatarColor?: string | null;
  avatarIcon?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function AgentAvatar({
  name,
  avatarColor = 'violet',
  avatarIcon = 'bot',
  size = 'md',
  className,
}: AgentAvatarProps) {
  const letters = name ? name.slice(0, 2).toUpperCase() : 'AG';

  const sizeClasses = {
    sm: 'w-7 h-7 text-[10px]',
    md: 'w-10 h-10 text-xs',
    lg: 'w-14 h-14 text-sm font-bold',
  };

  const colorMap: Record<string, string> = {
    violet: 'bg-violet-600/20 text-violet-300 border-violet-500/30',
    blue: 'bg-blue-600/20 text-blue-300 border-blue-500/30',
    emerald: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/30',
    rose: 'bg-rose-600/20 text-rose-300 border-rose-500/30',
    amber: 'bg-amber-600/20 text-amber-300 border-amber-500/30',
    cyan: 'bg-cyan-600/20 text-cyan-300 border-cyan-500/30',
  };

  const resolvedColor = avatarColor || 'violet';
  const selectedColor = colorMap[resolvedColor] || colorMap.violet;

  return (
    <div
      className={cn(
        'rounded-full border flex items-center justify-center shrink-0 font-mono font-bold select-none shadow-md',
        selectedColor,
        sizeClasses[size],
        className
      )}
    >
      {letters}
    </div>
  );
}

interface StatusBadgeProps {
  status: AgentStatus | AgentRunStatus;
  className?: string;
}

export function AgentStatusBadge({ status, className }: StatusBadgeProps) {
  const badgeConfig: Record<
    string,
    { label: string; icon: any; classes: string }
  > = {
    // Agent status
    ACTIVE: { label: 'Active', icon: CheckCircle2, classes: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' },
    INACTIVE: { label: 'Inactive', icon: AlertCircle, classes: 'bg-neutral-800 border-white/5 text-neutral-500' },
    ARCHIVED: { label: 'Archived', icon: AlertCircle, classes: 'bg-amber-500/10 border-amber-500/20 text-amber-400' },

    // Run status
    PENDING: { label: 'Pending', icon: ClockIcon, classes: 'bg-neutral-800 border-white/5 text-neutral-400' },
    RUNNING: { label: 'Running', icon: Activity, classes: 'bg-violet-500/10 border-violet-500/20 text-violet-400 animate-pulse' },
    COMPLETED: { label: 'Completed', icon: CheckCircle2, classes: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' },
    FAILED: { label: 'Failed', icon: AlertCircle, classes: 'bg-rose-500/10 border-rose-500/20 text-rose-400' },
    CANCELLED: { label: 'Cancelled', icon: AlertCircle, classes: 'bg-neutral-800 border-white/5 text-neutral-400' },
  };

  const config = badgeConfig[status] || {
    label: status,
    icon: Bot,
    classes: 'bg-neutral-800 border-white/5 text-neutral-400',
  };

  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border text-[10px] font-semibold tracking-wide font-mono uppercase',
        config.classes,
        className
      )}
    >
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

function ClockIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
      className={cn('w-3 h-3', props.className)}
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}
