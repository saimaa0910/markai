'use client';

import * as React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Loader2, Sparkles } from 'lucide-react';
import { useUIStore } from '@/store/ui';

export function LoadingOverlay() {
  const { globalLoading } = useUIStore();

  return (
    <AnimatePresence>
      {globalLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/85 backdrop-blur-md select-none pointer-events-auto"
        >
          {/* Ambient Purple Glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[250px] h-[250px] rounded-full bg-violet-600/20 blur-[100px] animate-pulse pointer-events-none" />

          <div className="relative z-10 flex flex-col items-center gap-4">
            <div className="relative flex items-center justify-center">
              <Loader2 className="w-12 h-12 animate-spin text-violet-500" />
              <Sparkles className="w-5 h-5 text-violet-300 absolute animate-pulse" />
            </div>
            <div className="flex flex-col gap-1 text-center">
              <span className="text-sm font-bold tracking-tight text-white">Viptant AI Processing</span>
              <span className="text-[10px] text-neutral-400">Please wait while the action completes...</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
