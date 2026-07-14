'use client';

import * as React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    // Log the error to an analytics or error tracking service
    console.error('Unhandled runtime application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Background Gradients */}
      <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-violet-600/10 blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-rose-600/5 blur-[160px]" />

      <div className="relative z-10 max-w-md w-full bg-neutral-900/40 border border-white/10 rounded-2xl p-8 backdrop-blur-md shadow-2xl flex flex-col items-center text-center gap-6">
        <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
          <AlertTriangle className="w-6 h-6 animate-pulse" />
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-xl font-bold tracking-tight text-white">Something went wrong</h2>
          <p className="text-xs text-neutral-400 leading-relaxed">
            An unexpected error occurred in Viptant. Our technical team has been notified.
          </p>
          {error.message && (
            <div className="mt-3 p-3 rounded-lg bg-neutral-950/80 border border-white/5 font-mono text-[10px] text-rose-400 text-left overflow-x-auto max-w-full">
              {error.message}
            </div>
          )}
        </div>

        <div className="flex gap-3 w-full mt-2">
          <Button
            variant="outline"
            className="flex-1 text-xs gap-2"
            onClick={() => window.location.href = '/dashboard'}
          >
            <Home className="w-4 h-4" /> Go Home
          </Button>
          <Button
            variant="violet"
            className="flex-1 text-xs gap-2"
            onClick={reset}
          >
            <RefreshCw className="w-4 h-4" /> Try Again
          </Button>
        </div>
      </div>
    </div>
  );
}
