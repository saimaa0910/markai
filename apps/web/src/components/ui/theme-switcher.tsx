'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from './theme-provider';
import { cn } from '@eaimos/shared';

type Theme = 'light' | 'dark' | 'system';

const options: { value: Theme; icon: React.ReactNode; label: string }[] = [
  { value: 'light', icon: <Sun className="w-3.5 h-3.5" />, label: 'Light' },
  { value: 'dark', icon: <Moon className="w-3.5 h-3.5" />, label: 'Dark' },
  { value: 'system', icon: <Monitor className="w-3.5 h-3.5" />, label: 'System' },
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
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (variant === 'tabs') {
    return (
      <div
        className={cn(
          'flex items-center gap-0.5 p-1 rounded-lg bg-white/5 border border-white/8',
          className
        )}
      >
        {options.map((opt) => {
          const isActive = theme === opt.value;
          return (
            <motion.button
              key={opt.value}
              onClick={() => setTheme(opt.value)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={opt.label}
              className={cn(
                'relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-semibold transition-colors cursor-pointer',
                isActive
                  ? 'text-violet-400'
                  : 'text-neutral-500 hover:text-neutral-300'
              )}
            >
              {isActive && (
                <motion.span
                  layoutId="theme-tab-indicator"
                  className="absolute inset-0 bg-violet-600/15 border border-violet-500/20 rounded-md"
                  transition={{ type: 'spring', bounce: 0.25, duration: 0.35 }}
                />
              )}
              <span className="relative z-10">{opt.icon}</span>
              <span className="relative z-10 hidden sm:inline">{opt.label}</span>
            </motion.button>
          );
        })}
      </div>
    );
  }

  // Dropdown variant for compact spaces (navbar, user menu)
  const current = options.find((o) => o.value === theme) ?? options[1];

  return (
    <div ref={ref} className={cn('relative', className)}>
      <motion.button
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/8 bg-white/5 text-neutral-400 hover:text-white hover:border-violet-500/30 transition-all text-xs font-semibold cursor-pointer"
        title="Change theme"
      >
        {current.icon}
      </motion.button>

      {open && (
        <motion.div
          initial={{ opacity: 0, y: -6, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -6, scale: 0.96 }}
          className="absolute right-0 top-10 min-w-[130px] bg-neutral-900 border border-white/10 rounded-xl shadow-2xl z-50 p-1 flex flex-col gap-0.5"
        >
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
                  'flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer w-full text-left',
                  isActive
                    ? 'bg-violet-600/15 text-violet-400 border border-violet-500/20'
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                )}
              >
                {opt.icon}
                {opt.label}
              </button>
            );
          })}
        </motion.div>
      )}
    </div>
  );
}
