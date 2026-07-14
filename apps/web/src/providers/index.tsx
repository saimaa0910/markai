'use client';

import * as React from 'react';
import { QueryProvider } from './query-provider';
import { ToastProvider } from '@/components/ui/toast';
import { LoadingOverlay } from '@/components/ui/loading-overlay';
import { ProgressBarProvider } from '@/components/ui/progress-bar';
import { ThemeProvider } from '@/components/ui/theme-provider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <ProgressBarProvider>
          {children}
        </ProgressBarProvider>
        <ToastProvider />
        <LoadingOverlay />
      </QueryProvider>
    </ThemeProvider>
  );
}
