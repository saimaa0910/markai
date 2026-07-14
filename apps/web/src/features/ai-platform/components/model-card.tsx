import * as React from 'react';
import { motion } from 'framer-motion';
import { 
  Database, CheckCircle2, XCircle, Zap, DollarSign, 
  HelpCircle, Star, BarChart3, Columns 
} from 'lucide-react';
import { AIModel } from '../types';
import { useAIPlatformStore } from '../store/ai-platform';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toast';
import { useModels } from '../hooks';

interface ModelCardProps {
  model: AIModel;
  delay: number;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  groq: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  anthropic: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  google: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  openrouter: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
};

export function ModelCard({ model, delay }: ModelCardProps) {
  const { toggleHealth } = useModels();
  const { 
    favorites, toggleFavorite,
    comparisonModels, addToComparison, removeFromComparison 
  } = useAIPlatformStore();

  const isFavorite = favorites.includes(model.id);
  const isInComparison = comparisonModels.includes(model.id);

  const providerColor = PROVIDER_COLORS[model.provider] || 'bg-neutral-800 text-neutral-400 border-white/5';

  const handleToggleFavorite = () => {
    toggleFavorite(model.id);
    toast.success(
      isFavorite ? 'Removed Favorite' : 'Marked Favorite',
      `${model.name} has been ${isFavorite ? 'removed from' : 'added to'} your favorites.`
    );
  };

  const handleToggleComparison = () => {
    if (isInComparison) {
      removeFromComparison(model.id);
      toast.success('Removed from Comparison', `${model.name} removed from comparison matrix.`);
    } else {
      addToComparison(model.id);
      toast.success('Added to Comparison', `${model.name} added to comparison matrix (Max 3).`);
    }
  };

  const handleToggleHealth = () => {
    const nextHealth = !model.is_healthy;
    toggleHealth.mutate({ modelId: model.id, isHealthy: nextHealth }, {
      onSuccess: () => {
        toast.success(
          nextHealth ? 'Model Restored' : 'Model Degraded',
          `${model.name} health status has been overridden manually.`
        );
      }
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.2 }}
      className="glass rounded-xl p-5 flex flex-col gap-4 hover:border-violet-500/25 transition-all group duration-300 relative"
    >
      {/* Favorite Button */}
      <button 
        onClick={handleToggleFavorite}
        className="absolute top-4 right-4 text-neutral-600 hover:text-amber-400 transition-colors cursor-pointer"
      >
        <Star className={`w-4 h-4 ${isFavorite ? 'fill-amber-400 text-amber-400' : ''}`} />
      </button>

      {/* Header */}
      <div className="flex flex-col gap-1.5 pr-6">
        <div className="flex items-center gap-2">
          <Badge className={`capitalize border ${providerColor}`} size="sm">
            {model.provider}
          </Badge>
          <span className="text-[10px] font-mono text-neutral-500 font-bold">{model.model_name}</span>
        </div>
        <a href={`/dashboard/ai/models/${model.id}`} className="hover:text-violet-400 transition-colors hover:underline">
          <h3 className="font-bold text-white text-sm mt-0.5">{model.name}</h3>
        </a>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2.5 rounded-lg bg-neutral-950/40 border border-white/5 flex flex-col gap-0.5">
          <span className="text-[9px] text-neutral-500 uppercase font-semibold">Latency</span>
          <span className="font-mono font-semibold text-neutral-200">
            {Number(model.latency).toFixed(2)}s avg
          </span>
        </div>
        
        <div className="p-2.5 rounded-lg bg-neutral-950/40 border border-white/5 flex flex-col gap-0.5">
          <span className="text-[9px] text-neutral-500 uppercase font-semibold">Context Size</span>
          <span className="font-mono font-semibold text-neutral-200">
            {(model.context_window / 1000).toFixed(0)}k t
          </span>
        </div>
      </div>

      {/* Cost Metrics */}
      <div className="flex flex-col gap-1 text-xs">
        <span className="text-[10px] text-neutral-500 font-semibold">Token Prices (per 1k tokens)</span>
        <div className="flex items-center justify-between p-2 rounded-lg bg-neutral-950/20 border border-white/5">
          <div className="flex items-center gap-1 font-mono text-neutral-300">
            <span className="text-neutral-500 text-[10px]">In:</span>
            <b>${Number(model.input_token_price).toFixed(4)}</b>
          </div>
          <div className="w-px h-3 bg-white/5" />
          <div className="flex items-center gap-1 font-mono text-neutral-300">
            <span className="text-neutral-500 text-[10px]">Out:</span>
            <b>${Number(model.output_token_price).toFixed(4)}</b>
          </div>
        </div>
      </div>

      {/* Capabilities Checklist */}
      <div className="flex flex-col gap-1.5">
        <span className="text-[10px] text-neutral-500 font-semibold">Capabilities</span>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
          {[
            { label: 'Streaming', val: model.supports_streaming },
            { label: 'Vision', val: model.supports_vision },
            { label: 'JSON Mode', val: model.supports_json },
            { label: 'Tool Calls', val: model.supports_tool_calling },
            { label: 'Embeddings', val: model.supports_embeddings },
            { label: 'Images Output', val: model.supports_images }
          ].map((cap, i) => (
            <div key={i} className="flex items-center gap-1.5 text-neutral-400">
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cap.val ? 'bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.5)]' : 'bg-neutral-800'}`} />
              <span className={cap.val ? 'text-neutral-200' : 'text-neutral-600 line-through decoration-white/5'}>{cap.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between text-[11px] border-t border-white/5 pt-3 mt-1">
        <div className="flex items-center gap-1.5">
          {model.is_healthy ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          ) : (
            <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
          )}
          <span className={model.is_healthy ? 'text-emerald-400' : 'text-rose-400'}>
            {model.is_healthy ? 'Healthy status' : 'Degraded status'}
          </span>
        </div>
        
        <Badge variant={model.priority >= 10 ? 'violet' : 'neutral'} size="sm">
          Priority: {model.priority}
        </Badge>
      </div>

      {/* Quick controls */}
      <div className="flex items-center gap-2 border-t border-white/5 pt-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleToggleComparison}
          className={`flex-1 text-[11px] h-8 border-white/5 ${isInComparison ? 'bg-violet-600/10 text-violet-400 hover:bg-violet-600/20 hover:text-white border-violet-500/20' : 'bg-neutral-900/50 hover:bg-neutral-900 text-neutral-300'}`}
        >
          <Columns className="w-3 h-3 mr-1" />
          {isInComparison ? 'Comparing' : 'Compare'}
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          onClick={handleToggleHealth}
          disabled={toggleHealth.isPending}
          className={`text-[11px] h-8 px-2 border-white/5 ${model.is_healthy ? 'text-rose-400 hover:bg-rose-500/10' : 'text-emerald-400 hover:bg-emerald-500/10'}`}
        >
          {model.is_healthy ? 'Simulate Fail' : 'Restore Health'}
        </Button>
      </div>
    </motion.div>
  );
}
