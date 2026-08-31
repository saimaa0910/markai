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
    lg: { box: 'w-10 h-10', svg: 'w-6.5 h-6.5', text: 'text-2xl' },
  };

  const currentSize = sizeMap[size];

  const logoAnimation: Variants | undefined = animate
    ? {
        hover: { scale: 1.05, transition: { duration: 0.2 } },
        tap: { scale: 0.95 },
      }
    : undefined;

  return (
    <div
      onClick={onClick}
      className={cn(
        'flex items-center gap-2.5 cursor-pointer select-none group',
        className
      )}
    >
      {/* Official Viptant Company Emblem */}
      <motion.div
        variants={logoAnimation}
        whileHover={animate ? 'hover' : undefined}
        whileTap={animate ? 'tap' : undefined}
        className={cn(
          'relative rounded-xl bg-gradient-to-br from-violet-600 via-indigo-600 to-violet-700 flex items-center justify-center text-white shadow-lg transition-shadow duration-300',
          currentSize.box
        )}
        style={{
          boxShadow: `0 4px 14px ${BrandConfig.glowColor}`,
        }}
      >
        <svg
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={cn('text-white drop-shadow-sm', currentSize.svg)}
        >
          {/* Official Viptant Interlocking V-Emblem */}
          {/* Left top cap & inner diagonal branch */}
          <path
            d="M 16 18 H 42 V 30 H 28 L 50 72 L 62 48 L 74 54 L 50 96 L 16 30 Z"
            fill="currentColor"
          />
          {/* Right top cap & outer diagonal wing */}
          <path
            d="M 58 18 H 84 V 30 H 70 L 52 64 L 42 58 L 58 28 H 58 Z"
            fill="currentColor"
            fillOpacity="0.92"
          />
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
