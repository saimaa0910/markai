'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function GeneratorPage() {
  const router = useRouter();

  React.useEffect(() => {
    router.replace('/dashboard/ai');
  }, [router]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center text-white">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
        <span className="text-xs text-neutral-400">Loading AI Workspace...</span>
      </div>
    </div>
  );
}
