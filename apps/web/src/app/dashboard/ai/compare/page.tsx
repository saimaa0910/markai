'use client';

import * as React from 'react';
import { Suspense } from 'react';
import { ComparePage } from '@/features/ai-platform/pages/compare';

export default function AICompareRoute() {
  return (
    <Suspense fallback={<div className="p-8 text-neutral-400 text-xs animate-pulse">Loading Comparison Lab...</div>}>
      <ComparePage />
    </Suspense>
  );
}
