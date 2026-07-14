'use client';

import * as React from 'react';
import { ShieldAlert, RefreshCw, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function MaintenancePage() {
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Background Gradients */}
      <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-amber-500/5 blur-[120px] animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-violet-600/10 blur-[160px] animate-pulse" style={{ animationDuration: '8s' }} />

      <div className="relative z-10 max-w-md w-full bg-neutral-900/40 border border-white/10 rounded-2xl p-8 backdrop-blur-md shadow-2xl flex flex-col items-center text-center gap-6">
        <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
          <ShieldAlert className="w-6 h-6" />
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center justify-center gap-1.5">
            System Upgrades in Progress <Sparkles className="w-4 h-4 text-violet-400" />
          </h2>
          <p className="text-xs text-neutral-400 leading-relaxed">
            Viptant's AI marketing operating database is currently undergoing scheduled optimization to improve vector search pipelines. We will return shortly.
          </p>
        </div>

        <div className="p-3.5 rounded-lg border border-white/5 bg-neutral-950/60 text-[10px] text-neutral-500 w-full select-none">
          Estimated completion time: <strong className="text-neutral-300">Under 15 minutes</strong>
        </div>

        <Button
          variant="violet"
          className="w-full text-xs gap-2 mt-2"
          onClick={handleRefresh}
          isLoading={isRefreshing}
        >
          <RefreshCw className="w-4 h-4" /> Check System Status
        </Button>
      </div>
    </div>
  );
}
