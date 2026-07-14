import * as React from 'react';
import { useKnowledgeStore } from '../../store/knowledge';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { Settings, Save, Sliders, Info, Server } from 'lucide-react';
import { toast } from '@/components/ui/toast';

export function SettingsPage() {
  const store = useKnowledgeStore();

  const [chunkSize, setChunkSize] = React.useState(store.settings.chunk_size);
  const [chunkOverlap, setChunkOverlap] = React.useState(store.settings.chunk_overlap);
  const [model, setModel] = React.useState(store.settings.embedding_model);
  const [autoIndex, setAutoIndex] = React.useState(store.settings.auto_index);
  const [autoEmbed, setAutoEmbed] = React.useState(store.settings.auto_embed);
  const [duplicateDetect, setDuplicateDetect] = React.useState(store.settings.duplicate_detection);

  const handleSave = () => {
    if (chunkSize <= 50 || chunkOverlap >= chunkSize) {
      toast.error('Invalid Parameters', 'Overlap size must be strictly smaller than total chunk size.');
      return;
    }

    store.updateSettings({
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
      embedding_model: model,
      auto_index: autoIndex,
      auto_embed: autoEmbed,
      duplicate_detection: duplicateDetect,
    });

    toast.success('Settings Saved', 'Ingestion workflow parameters updated.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Knowledge Base Settings"
        description="Configure chunk dimensions, default model registry parameters, and ingestion automation options."
        icon={<Settings className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Ingestion settings</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* SETTINGS FORM (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card className="flex flex-col gap-5">
            <div>
              <h3 className="font-bold text-white text-sm">Ingestion Parameters</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Define structural parameters for text extraction pipelines.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-neutral-400 font-bold uppercase">Chunk Size (characters)</label>
                <Input
                  type="number"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(Number(e.target.value))}
                  className="bg-neutral-950 border-white/5 font-mono"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-neutral-400 font-bold uppercase">Chunk Overlap</label>
                <Input
                  type="number"
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(Number(e.target.value))}
                  className="bg-neutral-950 border-white/5 font-mono"
                />
              </div>

              <div className="flex flex-col gap-1.5 md:col-span-2">
                <label className="text-[10px] text-neutral-400 font-bold uppercase">Embedding Model</label>
                <Select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="bg-neutral-950 border-white/5 font-mono"
                  options={[
                    { label: 'text-embedding-3-small (1536 dim)', value: 'text-embedding-3-small' },
                    { label: 'text-embedding-3-large (3072 dim)', value: 'text-embedding-3-large' },
                    { label: 'nomic-embed-text (768 dim)', value: 'nomic-embed-text' },
                  ]}
                />
              </div>
            </div>

            <div className="border-t border-white/5 pt-4 flex flex-col gap-3.5">
              <span className="text-xs font-bold text-white">Pipeline Automation</span>
              
              <div className="flex items-center justify-between text-xs">
                <div className="flex flex-col gap-0.5">
                  <span className="font-semibold text-neutral-300">Auto Ingestion</span>
                  <span className="text-[10px] text-neutral-500">Trigger parsing flow automatically on file upload completion.</span>
                </div>
                <input
                  type="checkbox"
                  checked={autoIndex}
                  onChange={(e) => setAutoIndex(e.target.checked)}
                  className="w-4 h-4 rounded accent-violet-600 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex flex-col gap-0.5">
                  <span className="font-semibold text-neutral-300">Auto Embedding Generation</span>
                  <span className="text-[10px] text-neutral-500">Send chunks to OpenAI Embeddings gateway on extraction pass.</span>
                </div>
                <input
                  type="checkbox"
                  checked={autoEmbed}
                  onChange={(e) => setAutoEmbed(e.target.checked)}
                  className="w-4 h-4 rounded accent-violet-600 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex flex-col gap-0.5">
                  <span className="font-semibold text-neutral-300">Duplicate detection</span>
                  <span className="text-[10px] text-neutral-500">Crosscheck file checksums before processing.</span>
                </div>
                <input
                  type="checkbox"
                  checked={duplicateDetect}
                  onChange={(e) => setDuplicateDetect(e.target.checked)}
                  className="w-4 h-4 rounded accent-violet-600 cursor-pointer"
                />
              </div>
            </div>

            <div className="border-t border-white/5 pt-4 flex justify-end">
              <Button variant="violet" size="sm" onClick={handleSave} className="text-xs h-8">
                <Save className="w-3.5 h-3.5 mr-1" />
                Save Settings
              </Button>
            </div>
          </Card>
        </div>

        {/* RESOURCE LIMITS (Right 1 column) */}
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4 bg-neutral-950/20">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-violet-400" /> Storage Capacity Limits
            </span>

            <div className="flex flex-col gap-3.5 text-xs">
              <div className="flex flex-col gap-1">
                <span className="text-neutral-500">Workspace Allocated Disk</span>
                <span className="text-white font-bold font-mono">1.2 MB / 100 MB Used (1.2%)</span>
              </div>
              <div className="w-full bg-neutral-900 border border-white/5 h-1.5 rounded-full overflow-hidden">
                <div className="h-full bg-violet-600 rounded-full w-[1.2%]" />
              </div>
              <p className="text-[10px] text-neutral-500 leading-normal">
                Contact your workspace administrator to upgrade limits bounds.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
export { Sliders, Info };
