import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Hash, Key, ArrowRightLeft } from 'lucide-react';

interface TokenCounterProps {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  label?: string;
}

export function TokenCounter({ promptTokens, completionTokens, totalTokens, label }: TokenCounterProps) {
  return (
    <div className="rounded-xl border border-white/5 bg-neutral-950/20 p-4 flex flex-col gap-3">
      {label && <span className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">{label}</span>}
      <div className="grid grid-cols-3 gap-2">
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] text-neutral-500 flex items-center gap-1">
            <Hash className="w-3 h-3 text-neutral-600" /> Input
          </span>
          <motion.span 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-sm font-mono font-bold text-neutral-300"
          >
            {promptTokens.toLocaleString()}
          </motion.span>
        </div>
        
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] text-neutral-500 flex items-center gap-1">
            <Hash className="w-3 h-3 text-neutral-600" /> Output
          </span>
          <motion.span 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-sm font-mono font-bold text-neutral-300"
          >
            {completionTokens.toLocaleString()}
          </motion.span>
        </div>

        <div className="flex flex-col gap-0.5 border-l border-white/5 pl-3">
          <span className="text-[10px] text-neutral-400 font-medium flex items-center gap-1">
            <ArrowRightLeft className="w-3 h-3 text-violet-400" /> Total
          </span>
          <motion.span 
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-sm font-mono font-bold text-violet-400"
          >
            {totalTokens.toLocaleString()}
          </motion.span>
        </div>
      </div>
    </div>
  );
}
