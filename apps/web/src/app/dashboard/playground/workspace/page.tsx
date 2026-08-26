'use client';

import * as React from 'react';
import { Suspense } from 'react';
import { PlaygroundPage } from '@/features/ai-platform/pages/playground';

export default function AIWorkspaceRoute() {
  return (
    <Suspense fallback={<div className="p-8 text-neutral-400 text-xs animate-pulse">Loading AI Workspace...</div>}>
      <PlaygroundPage />
    </Suspense>
  );
}
