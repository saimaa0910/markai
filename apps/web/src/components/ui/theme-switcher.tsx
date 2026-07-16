'use client';

import * as React from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from './theme-provider';
import { cn } from '@eaimos/shared';

type Theme = 'light' | 'dark' | 'system';

const options: { value: Theme; icon: React.ReactNode; label: string }[] = [
  { value: 'light', icon: <Sun className="h-3.5 w-3.5" />, label: 'Light' },
  { value: 'dark', icon: <Moon className="h-3.5 w-3.5" />, label: 'Dark' },
  { value: 'system', icon: <Monitor className="h-3.5 w-3.5" />, label: 'System' },
];

interface ThemeSwitcherProps {
  variant?: 'tabs' | 'dropdown';
  className?: string;
}

export function ThemeSwitcher({ variant = 'tabs', className }: ThemeSwitcherProps) {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (variant === 'tabs') {
    return (
      <div className={cn('flex items-center gap-0.5 rounded-lg border border-border bg-card p-1 shadow-soft', className)}>
        {options.map((opt) => {
          const isActive = theme === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => setTheme(opt.value)}
              title={opt.label}
              className={cn(
                'relative flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold transition-colors cursor-pointer',
                isActive ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <span>{opt.icon}</span>
              <span className="hidden sm:inline">{opt.label}</span>
            </button>
          );
        })}
      </div>
    );
  }

  const current = options.find((option) => option.value === theme) ?? options[1];

  return (
    <div ref={ref} className={cn('relative', className)}>
      <button
        onClick={() => setOpen((value) => !value)}
        className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 py-1.5 text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground"
        title="Change theme"
      >
        {current.icon}
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-50 flex min-w-[130px] flex-col gap-0.5 rounded-xl border border-border bg-card p-1 shadow-card">
          {options.map((opt) => {
            const isActive = theme === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => {
                  setTheme(opt.value);
                  setOpen(false);
                }}
                className={cn(
                  'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-xs font-semibold transition-colors cursor-pointer',
                  isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                )}
              >
                {opt.icon}
                {opt.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
