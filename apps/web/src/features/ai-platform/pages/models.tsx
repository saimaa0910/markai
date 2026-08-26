import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useModels } from '../hooks';
import { ModelCard } from '../components/model-card';
import { FilterPanel } from '../components/filter-panel';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DataTable, DataTableColumn } from '@/components/ui/data-table';
import { useAIPlatformStore } from '../store/ai-platform';
import { Database, Columns, Check, Star, RefreshCw, X, Zap, Cpu, ArrowRight, Play } from 'lucide-react';
import { toast } from '@/components/ui/toast';

export function ModelsPage() {
  const router = useRouter();
  const { models, isLoading, refetch, toggleHealth } = useModels();
  const { 
    searchQuery, selectedProvider, selectedModel,
    viewPreference, timeRange, favorites,
    comparisonModels, removeFromComparison, clearComparison
  } = useAIPlatformStore();

  const [showOnlyFavorites, setShowOnlyFavorites] = React.useState(false);

  // Filter models based on state
  const filteredModels = React.useMemo(() => {
    return models.filter((m) => {
      if (selectedProvider && m.provider !== selectedProvider) return false;
      if (selectedModel && m.model_name !== selectedModel) return false;
      if (showOnlyFavorites && !favorites.includes(m.id)) return false;
      
      if (searchQuery) {
        const q = (searchQuery || '').toLowerCase();
        return (m?.name || '').toLowerCase().includes(q) || 
               (m?.model_name || '').toLowerCase().includes(q) ||
               (m?.provider || '').toLowerCase().includes(q);
      }
      return true;
    });
  }, [models, selectedProvider, selectedModel, searchQuery, showOnlyFavorites, favorites]);

  // Model comparison metadata
  const selectedComparisonModels = React.useMemo(() => {
    return models.filter((m) => comparisonModels.includes(m.id));
  }, [models, comparisonModels]);

  const handleOpenCompareLab = () => {
    if (selectedComparisonModels.length === 0) return;
    const modelNames = selectedComparisonModels.map((m) => m.model_name).join(',');
    router.push(`/dashboard/ai/compare?models=${encodeURIComponent(modelNames)}`);
  };

  const columns: DataTableColumn<any>[] = [
    {
      key: 'name',
      label: 'Model Name',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5 text-violet-400 shrink-0" />
          <div className="flex flex-col">
            <a 
              href={`/dashboard/ai/models/${row.id}`} 
              className="font-semibold text-white text-xs hover:text-violet-400 transition-colors hover:underline"
            >
              {row.name}
            </a>
            <span className="text-[10px] text-neutral-500 font-mono">{row.model_name}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'provider',
      label: 'Provider',
      sortable: true,
      render: (row) => (
        <Badge variant="violet" className="capitalize text-[10px]">{row.provider}</Badge>
      ),
    },
    {
      key: 'context_window',
      label: 'Context',
      sortable: true,
      render: (row) => (
        <span className="text-xs text-neutral-300 font-mono">{(row.context_window / 1000).toFixed(0)}k tokens</span>
      ),
    },
    {
      key: 'input_token_price',
      label: 'In / 1k tokens',
      render: (row) => (
        <span className="text-xs font-mono text-neutral-300">${Number(row.input_token_price).toFixed(4)}</span>
      ),
    },
    {
      key: 'output_token_price',
      label: 'Out / 1k tokens',
      render: (row) => (
        <span className="text-xs font-mono text-neutral-300">${Number(row.output_token_price).toFixed(4)}</span>
      ),
    },
    {
      key: 'latency',
      label: 'Latency',
      sortable: true,
      render: (row) => (
        <Badge variant={row.latency < 0.3 ? 'emerald' : 'amber'} className="font-mono text-[10px]">
          {Number(row.latency).toFixed(2)}s
        </Badge>
      ),
    },
    {
      key: 'is_healthy',
      label: 'Status',
      render: (row) => (
        <Badge variant={row.is_healthy ? 'emerald' : 'rose'} dot>
          {row.is_healthy ? 'Healthy' : 'Failing'}
        </Badge>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Model Registry"
        description="View and compare capabilities, latency limits, context sizes, and pricing configurations of all models registered in the gateway."
        icon={<Database className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">{models.length} Models</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowOnlyFavorites(!showOnlyFavorites);
                toast.success(
                  showOnlyFavorites ? 'Showing all models' : 'Showing favorite models',
                  showOnlyFavorites ? 'Standard list restored.' : 'Filtering registry list.'
                );
              }}
              className={`h-9 text-[11px] border-white/5 ${showOnlyFavorites ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-neutral-900/50 hover:bg-neutral-900'}`}
            >
              <Star className={`w-3.5 h-3.5 mr-1.5 ${showOnlyFavorites ? 'fill-amber-400' : ''}`} />
              Favorites ({favorites.length})
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="h-9 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
          </div>
        }
      />

      {/* Model comparison matrix display */}
      {selectedComparisonModels.length > 0 && (
        <div className="glass border-violet-500/20 rounded-2xl p-5 flex flex-col gap-4 relative animate-in fade-in slide-in-from-top-4 duration-300">
          <button 
            onClick={clearComparison}
            className="absolute top-4 right-4 text-neutral-500 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
          
          <div className="flex items-center justify-between pr-8">
            <div>
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                Model Comparison Matrix <Columns className="w-4 h-4 text-violet-400" />
              </h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Comparing up to 3 selected models side-by-side.</p>
            </div>
            <Button
              variant="violet"
              size="sm"
              onClick={handleOpenCompareLab}
              className="h-8 text-xs px-3 shadow-sm flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5" />
              Open in Compare Lab
              <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border border-white/5 bg-neutral-950/20 p-4 rounded-xl">
            {selectedComparisonModels.map((m) => (
              <div key={m.id} className="flex flex-col gap-3 relative border-r border-white/5 last:border-none pr-4 last:pr-0">
                <button 
                  onClick={() => removeFromComparison(m.id)}
                  className="absolute top-0 right-0 text-neutral-500 hover:text-rose-400 transition-colors cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
                
                <div className="flex flex-col gap-0.5">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-mono">{m.provider}</span>
                  <h4 className="font-bold text-white text-xs">{m.name}</h4>
                </div>

                <div className="flex flex-col gap-1 border-t border-white/5 pt-2 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Latency:</span>
                    <span className="font-mono text-neutral-300">{Number(m.latency).toFixed(2)}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Context Window:</span>
                    <span className="font-mono text-neutral-300">{(m.context_window / 1000).toFixed(0)}k tokens</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Input / 1k:</span>
                    <span className="font-mono text-emerald-400">${Number(m.input_token_price).toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Output / 1k:</span>
                    <span className="font-mono text-emerald-400">${Number(m.output_token_price).toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Streaming:</span>
                    <span className="font-bold">{m.supports_streaming ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Vision support:</span>
                    <span className="font-bold">{m.supports_vision ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Tool Calls:</span>
                    <span className="font-bold">{m.supports_tool_calling ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter and view preferences */}
      <FilterPanel onRefresh={refetch} />

      {/* Grid or Table display based on viewPreference store settings */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-44 rounded-xl border border-white/5 bg-neutral-900/20 animate-pulse" />
          ))}
        </div>
      ) : filteredModels.length > 0 ? (
        viewPreference === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredModels.map((m, idx) => (
              <ModelCard key={m.id} model={m} delay={idx * 0.03} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-white/5 overflow-hidden">
            <DataTable
              columns={columns}
              data={filteredModels}
              isLoading={isLoading}
              pageSize={10}
              searchable={false}
              actions={(row) => (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const next = !row.is_healthy;
                      toggleHealth.mutate({ modelId: row.id, isHealthy: next }, {
                        onSuccess: () => toast.success('Model status updated', `${row.name} updated.`)
                      });
                    }}
                    className={`h-7 text-[10px] ${row.is_healthy ? 'text-rose-400 border-rose-500/10' : 'text-emerald-400 border-emerald-500/10'}`}
                  >
                    {row.is_healthy ? 'Mark Down' : 'Mark Healthy'}
                  </Button>
                </div>
              )}
            />
          </div>
        )
      ) : (
        <div className="flex flex-col items-center justify-center text-center py-20 border border-dashed border-white/5 rounded-2xl bg-neutral-950/20">
          <Database className="w-8 h-8 text-neutral-600 mb-3" />
          <h3 className="font-bold text-white text-sm">No Models Configured</h3>
          <p className="text-xs text-neutral-500 max-w-xs mt-1">
            Try adjusting your search criteria, select a different provider, or restart backend service.
          </p>
        </div>
      )}
    </div>
  );
}
