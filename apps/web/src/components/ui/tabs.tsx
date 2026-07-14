'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';

// ─────────────────────────────────────────────────────────────────────────────
// Tabs Context
// ─────────────────────────────────────────────────────────────────────────────
interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}
const TabsContext = React.createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error('Tabs sub-components must be used inside <Tabs>');
  return ctx;
}

// ─────────────────────────────────────────────────────────────────────────────
// <Tabs> Root
// ─────────────────────────────────────────────────────────────────────────────
export interface TabsProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}

export function Tabs({ value, onValueChange, children, className }: TabsProps) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={cn('flex flex-col gap-4', className)}>{children}</div>
    </TabsContext.Provider>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// <TabsList> — pill container
// ─────────────────────────────────────────────────────────────────────────────
export function TabsList({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex items-center gap-0.5 rounded-lg bg-neutral-900 border border-white/5 p-1 self-start',
        className
      )}
      role="tablist"
    >
      {children}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// <TabsTrigger> — individual tab button
// ─────────────────────────────────────────────────────────────────────────────
export interface TabsTriggerProps {
  value: string;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  icon?: React.ReactNode;
}

export function TabsTrigger({
  value,
  children,
  className,
  disabled,
  icon,
}: TabsTriggerProps) {
  const { value: activeValue, onValueChange } = useTabsContext();
  const isActive = activeValue === value;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      disabled={disabled}
      onClick={() => onValueChange(value)}
      className={cn(
        'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-all cursor-pointer select-none whitespace-nowrap',
        isActive
          ? 'bg-violet-600 text-white shadow'
          : 'text-neutral-400 hover:text-white hover:bg-white/5',
        disabled && 'opacity-40 pointer-events-none',
        className
      )}
    >
      {icon && <span className="w-3.5 h-3.5 shrink-0">{icon}</span>}
      {children}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// <TabsContent> — content panel
// ─────────────────────────────────────────────────────────────────────────────
export interface TabsContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const { value: activeValue } = useTabsContext();
  if (activeValue !== value) return null;
  return <div className={cn('flex flex-col gap-4', className)}>{children}</div>;
}
