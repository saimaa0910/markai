'use client';

import * as React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@eaimos/shared';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'ref' | 'children'> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'violet';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
  children?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading = false, children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 disabled:opacity-50 disabled:pointer-events-none cursor-pointer';
    
    const variants = {
      primary: 'bg-white text-black hover:bg-neutral-200 shadow-sm border border-neutral-200/20',
      violet: 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white hover:from-violet-500 hover:to-indigo-500 shadow-lg shadow-violet-500/20',
      secondary: 'bg-neutral-900 border border-white/10 text-white hover:bg-neutral-800',
      outline: 'bg-transparent border border-white/10 text-white hover:bg-white/5',
      ghost: 'bg-transparent text-neutral-400 hover:text-white hover:bg-white/5',
      destructive: 'bg-rose-600 text-white hover:bg-rose-500 shadow-sm',
    };
    
    const sizes = {
      sm: 'text-xs px-3 py-1.5 gap-1.5 h-8',
      md: 'text-sm px-4 py-2.5 gap-2 h-10',
      lg: 'text-base px-6 py-3 gap-2.5 h-12',
      icon: 'h-10 w-10 p-0',
    };

    return (
      <motion.button
        ref={ref}
        whileTap={{ scale: 0.98 }}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin text-current" />}
        {!isLoading && children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
