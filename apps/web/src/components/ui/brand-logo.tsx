'use client';

import * as React from 'react';
import { motion, Variants } from 'framer-motion';
import { BrandConfig } from './brand-config';
import { cn } from '@eaimos/shared';

interface BrandLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  animate?: boolean;
  className?: string;
  onClick?: () => void;
}

export function BrandLogo({
  size = 'md',
  showText = true,
  animate = true,
  className,
  onClick,
}: BrandLogoProps) {
  const sizeMap = {
    sm: { box: 'w-7 h-7', svg: 'w-4 h-4', text: 'text-base' },
    md: { box: 'w-8.5 h-8.5', svg: 'w-5 h-5', text: 'text-xl' },
    lg: { box: 'w-10 h-10', svg: 'w-6 h-6', text: 'text-2xl' },
  };

  const currentSize = sizeMap[size];

  const logoAnimation: Variants | undefined = animate
    ? {
        hover: { scale: 1.05, rotate: [0, -5, 5, 0], transition: { duration: 0.4 } },
        tap: { scale: 0.95 },
      }
    : undefined;

  const paths = [
    { d: 'M12 2L2 22h20L12 2z', fill: 'url(#brandGrad1)' },
    { d: 'M12 6l-6 12h12L12 6z', fill: 'url(#brandGrad2)' },
  ];

  return (
    <div
      onClick={onClick}
      className={cn(
        'flex items-center gap-2.5 cursor-pointer select-none group',
        className
      )}
    >
      {/* Dynamic Emblem */}
      <motion.div
        variants={logoAnimation}
        whileHover={animate ? 'hover' : undefined}
        whileTap={animate ? 'tap' : undefined}
        className={cn(
          'relative rounded-xl bg-gradient-to-br from-violet-600 via-indigo-600 to-violet-700 flex items-center justify-center font-bold text-white shadow-lg transition-shadow duration-300',
          currentSize.box
        )}
        style={{
          boxShadow: `0 4px 14px ${BrandConfig.glowColor}`,
        }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={cn('text-white drop-shadow-md', currentSize.svg)}
        >
          <defs>
            <linearGradient id="brandGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.3" />
            </linearGradient>
            <linearGradient id="brandGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#c084fc" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.4" />
            </linearGradient>
          </defs>
          <path d="M12 3L4 19h16L12 3zm0 4.5L17.5 17h-11L12 7.5z" fill="url(#brandGrad1)" />
          <circle cx="12" cy="13" r="2.5" fill="url(#brandGrad2)" />
        </svg>
      </motion.div>

      {/* Brand Text */}
      {showText && (
        <span
          className={cn(
            'font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-500 dark:from-white dark:via-neutral-100 dark:to-neutral-400 font-sans transition-colors duration-300',
            currentSize.text
          )}
        >
          {BrandConfig.name.toLowerCase()}
        </span>
      )}
    </div>
  );
}
