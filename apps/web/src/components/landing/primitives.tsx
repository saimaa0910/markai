'use client';

import * as React from 'react';
import { motion } from 'framer-motion';

// ─── Reusable section animation wrapper ─────────────────────────────────────
export function FadeUp({
  children,
  delay = 0,
  className = '',
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ─── Gradient heading text ───────────────────────────────────────────────────
export function GradientHeading({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h2
      className={`bg-clip-text text-transparent bg-gradient-to-r from-white via-neutral-200 to-neutral-400 ${className}`}
    >
      {children}
    </h2>
  );
}

// ─── Section label chip ──────────────────────────────────────────────────────
export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/20 bg-violet-500/5 text-violet-400 text-xs font-semibold uppercase tracking-widest mb-4">
      {children}
    </div>
  );
}

// ─── Stat card ───────────────────────────────────────────────────────────────
export function StatCard({
  value,
  label,
  suffix = '',
}: {
  value: string;
  label: string;
  suffix?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
        {value}
        <span className="text-violet-400">{suffix}</span>
      </span>
      <span className="text-sm text-neutral-400">{label}</span>
    </div>
  );
}
