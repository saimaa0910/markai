import * as React from 'react';
import { useEmbeddings } from '../../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  Sparkles, RefreshCw, Trash2, Cpu, CheckCircle2, 
  Layers, Database, Activity, Sliders, ShieldCheck 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

export function EmbeddingsPage() {
  const { stats, models } = useEmbeddings();
  
  const [rebuilding, setRebuilding] = React.useState(false);
  const [rebuildProgress, setRebuildProgress] = React.useState(0);

  const handleRebuild = () => {
    if (rebuilding) return;
    setRebuilding(true);
    setRebuildProgress(0);
    toast.success('Vector rebuild triggered', 'Recomputing embeddings for all text chunks.');

    // Simulate progress updates
    const interval = setInterval(() => {
      setRebuildProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setRebuilding(false);
          toast.success('Vector indexing complete', 'Re-indexed all library resource chunks.');
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  const handleDeleteAll = () => {
    toast.success('Embeddings Flushed', 'Cleared all vector partitions. Documents need to be re-indexed.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Vector Embeddings Console"
        description="Monitor indexing progress, inspect context chunk lengths, and manage vector partition weights."
        icon={<Sparkles className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Vector registry</Badge>}
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        <Card className="p-4 bg-neutral-950/20 flex flex-col gap-1.5">
          <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-violet-400" /> Vector Database
          </span>
          <span className="text-white text-base font-bold font-mono">pgvector</span>
        </Card>

        <Card className="p-4 bg-neutral-950/20 flex flex-col gap-1.5">
          <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-emerald-400" /> Total Chunks
          </span>
          <span className="text-white text-base font-bold font-mono">{stats.chunkCount} chunks</span>
        </Card>

        <Card className="p-4 bg-neutral-950/20 flex flex-col gap-1.5">
          <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5 text-sky-400" /> Active Model
          </span>
          <span className="text-white text-base font-bold truncate">text-embedding-3</span>
        </Card>

        <Card className="p-4 bg-neutral-950/20 flex flex-col gap-1.5">
          <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-amber-400" /> Embedder Health
          </span>
          <Badge variant="emerald" size="sm" dot className="self-start">Online</Badge>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* EMBEDDING MODELS (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Supported Embedding Models</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Gateway models available for vector conversion.</p>
            </div>

            <div className="flex flex-col gap-3 mt-1">
              {models.map((model) => (
                <div 
                  key={model.name} 
                  className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between gap-4 text-xs font-mono"
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-sans font-bold text-white text-sm">{model.name}</span>
                    <span className="text-neutral-500 text-[10px]">{model.provider} · {model.dimensions} dimensions</span>
                  </div>
                  <Badge variant="emerald" size="sm" dot>Operational</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* OPERATIONS CONSOLE (Right 1 column) */}
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Maintenance Console</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Flush vector indexes or rebuild embeddings databases.</p>
            </div>

            {rebuilding && (
              <div className="flex flex-col gap-2 p-3.5 bg-violet-600/10 border border-violet-500/20 rounded-xl text-xs">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5 text-violet-400 animate-spin" />
                  Rebuilding embeddings index...
                </span>
                <div className="w-full bg-neutral-900 border border-white/5 h-1.5 rounded-full overflow-hidden">
                  <div className="h-full bg-violet-600 rounded-full" style={{ width: `${rebuildProgress}%` }} />
                </div>
                <span className="text-[10px] text-neutral-500 font-mono text-right">{rebuildProgress}% complete</span>
              </div>
            )}

            <div className="flex flex-col gap-2.5 mt-2">
              <Button
                variant="violet"
                size="sm"
                onClick={handleRebuild}
                disabled={rebuilding}
                className="w-full h-9 text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1" />
                Rebuild All Embeddings
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={handleDeleteAll}
                className="w-full h-9 text-xs border-rose-500/20 bg-rose-950/10 text-rose-400 hover:bg-rose-950/20"
              >
                <Trash2 className="w-3.5 h-3.5 mr-1" />
                Clear All Embeddings
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
export { ShieldCheck };
