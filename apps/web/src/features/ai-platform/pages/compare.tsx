import * as React from 'react';
import { useSearchParams } from 'next/navigation';
import { useModels } from '../hooks';
import { useAIPlatformStore } from '../store/ai-platform';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { apiClient } from '@/services/api-client';
import { 
  Columns, Sparkles, Zap, DollarSign, BrainCircuit, Play, 
  HelpCircle, ChevronRight, CheckCircle2, AlertTriangle, ShieldCheck 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

interface ModelComparisonState {
  modelName: string;
  modelIdentifier: string;
  provider: string;
  latencySec: number;
  tokensPerSec: number;
  costUsd: number;
  tokensCount: number;
  response: string;
  isGenerating: boolean;
  qualityScore: number;
}

export function ComparePage() {
  const searchParams = useSearchParams();
  const { models } = useModels();
  const { comparisonModels } = useAIPlatformStore();
  const [activeCategory, setActiveCategory] = React.useState<'text' | 'image'>('text');
  const [selectedIds, setSelectedIds] = React.useState<string[]>([]);
  const [prompt, setPrompt] = React.useState('Explain recursion simply with a short code example.');
  const [comparisonList, setComparisonList] = React.useState<ModelComparisonState[]>([]);
  const [isRunning, setIsRunning] = React.useState(false);
  const [hasInitializedFromRoute, setHasInitializedFromRoute] = React.useState(false);

  // Set models on load from URL query params, store, or defaults
  React.useEffect(() => {
    if (models.length === 0) return;

    const routeModelsParam = searchParams.get('models');
    if (routeModelsParam && !hasInitializedFromRoute) {
      const requested = routeModelsParam.split(',').map((s) => decodeURIComponent((s || '').trim().toLowerCase()));
      const matched = models.filter((m) => 
        (m?.model_name && requested.includes(m.model_name.toLowerCase())) || 
        (m?.name && requested.includes(m.name.toLowerCase())) || 
        (m?.id && requested.includes(m.id.toLowerCase()))
      );
      if (matched.length > 0) {
        setSelectedIds(matched.slice(0, 3).map((m) => m.id));
        setHasInitializedFromRoute(true);
        return;
      }
    }

    if (comparisonModels.length > 0 && !hasInitializedFromRoute) {
      const matched = models.filter((m) => comparisonModels.includes(m.id));
      if (matched.length > 0) {
        setSelectedIds(matched.slice(0, 3).map((m) => m.id));
        setHasInitializedFromRoute(true);
        return;
      }
    }

    if (!hasInitializedFromRoute) {
      if (activeCategory === 'image') {
        const imageModels = models.filter((m) => m.supports_images).slice(0, 3);
        setSelectedIds(imageModels.map((m) => m.id));
      } else {
        const chatModels = models.filter((m) => m.supports_streaming).slice(0, 3);
        setSelectedIds(chatModels.map((m) => m.id));
      }
      setHasInitializedFromRoute(true);
    }
  }, [models, searchParams, comparisonModels, activeCategory, hasInitializedFromRoute]);

  const handleCheckboxToggle = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length <= 1) {
        toast.error('Selection Limit', 'Select at least 1 model to compare.');
        return;
      }
      setSelectedIds(selectedIds.filter((x) => x !== id));
    } else {
      if (selectedIds.length >= 3) {
        toast.error('Selection Limit', 'You can compare up to 3 models side-by-side.');
        return;
      }
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleRunComparison = async () => {
    if (isRunning) return;
    setIsRunning(true);
    toast.info('Inference Started', `Spawning comparison for ${selectedIds.length} models...`);

    const selectedModels = models.filter((m) => selectedIds.includes(m.id));
    const initialList: ModelComparisonState[] = selectedModels.map((m) => {
      return {
        modelName: m.name,
        modelIdentifier: m.model_name,
        provider: m.provider,
        latencySec: 0,
        tokensPerSec: 0,
        costUsd: 0,
        tokensCount: 0,
        response: '',
        isGenerating: true,
        qualityScore: 75,
      };
    });

    setComparisonList(initialList);

    try {
      const modelNames = selectedModels.map((m) => m.model_name);
      const res = await apiClient.post('/ai/compare/', {
        prompt,
        model_names: modelNames,
        category: activeCategory
      });

      const results = res.data.results || [];
      const updatedList: ModelComparisonState[] = selectedModels.map((m) => {
        const matchingResult = results.find((r: any) => r.model_name === m.model_name);
        if (matchingResult && matchingResult.status === 'success') {
          const totalTokens = matchingResult.prompt_tokens + matchingResult.completion_tokens;
          const latencySec = matchingResult.latency_ms / 1000;
          return {
            modelName: m.name,
            modelIdentifier: m.model_name,
            provider: m.provider,
            latencySec,
            tokensPerSec: latencySec > 0 ? Math.round(matchingResult.completion_tokens / latencySec) : 0,
            costUsd: matchingResult.cost_usd,
            tokensCount: totalTokens,
            response: matchingResult.response,
            isGenerating: false,
            qualityScore: m.provider === 'openai' ? 92 : m.provider === 'anthropic' ? 95 : 80,
          };
        } else {
          return {
            modelName: m.name,
            modelIdentifier: m.model_name,
            provider: m.provider,
            latencySec: 0,
            tokensPerSec: 0,
            costUsd: 0,
            tokensCount: 0,
            response: matchingResult?.error_message || 'Inference failed.',
            isGenerating: false,
            qualityScore: 0,
          };
        }
      });

      setComparisonList(updatedList);
      toast.success('Comparison Finished', 'All model inferences completed.');
    } catch (err: any) {
      toast.error('Comparison Failed', err?.message || 'Error occurred calling model registry.');
      setComparisonList(prev => prev.map(item => ({ ...item, isGenerating: false, response: 'Error running comparison.' })));
    } finally {
      setIsRunning(false);
    }
  };

  const [selectedProviderFilter, setSelectedProviderFilter] = React.useState<string>('all');

  const availableProviders = React.useMemo(() => {
    const activeModels = (models || []).filter((m) => activeCategory === 'image' ? m?.supports_images : m?.supports_streaming);
    const provs = Array.from(new Set(activeModels.map((m) => (m?.provider || '').toLowerCase()).filter(Boolean)));
    return ['all', ...provs];
  }, [models, activeCategory]);

  const selectableModels = React.useMemo(() => {
    return (models || [])
      .filter((m) => activeCategory === 'image' ? m?.supports_images : m?.supports_streaming)
      .filter((m) => selectedProviderFilter === 'all' || (m?.provider || '').toLowerCase() === (selectedProviderFilter || '').toLowerCase());
  }, [models, activeCategory, selectedProviderFilter]);

  const currentlySelectedModels = React.useMemo(() => {
    return models.filter((m) => selectedIds.includes(m.id));
  }, [models, selectedIds]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Model Comparison Lab"
        description="Submit a prompt to multiple models in parallel to evaluate differences in latency, token counts, costs, and output styles."
        icon={<Columns className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Performance Lab</Badge>}
      />

      {/* Capability Tabs */}
      <div className="flex gap-2 border-b border-white/5 pb-2 mb-2">
        <Button
          variant="ghost"
          onClick={() => {
            setActiveCategory('text');
            setSelectedProviderFilter('all');
            setPrompt('Explain recursion simply with a short code example.');
            setComparisonList([]);
          }}
          className={`px-4 py-2 text-xs border-b-2 rounded-none hover:bg-transparent ${
            activeCategory === 'text' 
              ? 'border-violet-500 text-violet-400 font-bold' 
              : 'border-transparent text-neutral-400'
          }`}
        >
          Text Inferences
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            setActiveCategory('image');
            setSelectedProviderFilter('all');
            setPrompt('A futuristic high-tech neon cyber city at night, masterpiece, photorealistic.');
            setComparisonList([]);
          }}
          className={`px-4 py-2 text-xs border-b-2 rounded-none hover:bg-transparent ${
            activeCategory === 'image' 
              ? 'border-violet-500 text-violet-400 font-bold' 
              : 'border-transparent text-neutral-400'
          }`}
        >
          Image Generation
        </Button>
      </div>

      {/* Comparing Models Header Banner */}
      {currentlySelectedModels.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border border-violet-500/20 bg-violet-950/20 backdrop-blur-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-white flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-400" />
              Comparing Models ({currentlySelectedModels.length}):
            </span>
            {currentlySelectedModels.map((m) => (
              <Badge key={m.id} variant="violet" className="font-mono text-[11px] py-0.5 flex items-center gap-1">
                <span className="font-bold text-white">{m.model_name}</span>
                <span className="text-violet-300/60 font-sans text-[10px]">({m.provider})</span>
              </Badge>
            ))}
          </div>
          <span className="text-[11px] font-mono text-neutral-400">
            {activeCategory === 'image' ? 'Image Generation Mode' : 'Streaming Chat Mode'}
          </span>
        </div>
      )}

      {/* Models Selection Card with Provider Filter */}
      <Card className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/5 pb-3">
          <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">
            Select up to 3 models to compare <span className="text-violet-400 font-mono">({selectedIds.length}/3 selected)</span>
          </span>

          {/* Provider Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] text-neutral-500 font-medium mr-1">Filter Provider:</span>
            {availableProviders.map((p) => (
              <button
                key={p}
                onClick={() => setSelectedProviderFilter(p)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium capitalize transition-all cursor-pointer ${
                  selectedProviderFilter === p
                    ? 'bg-violet-600/20 text-violet-400 border border-violet-500/40 shadow-sm'
                    : 'bg-neutral-900/60 text-neutral-400 hover:text-white border border-white/5'
                }`}
              >
                {p === 'all' ? 'All Providers' : p}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          {selectableModels.map((m) => {
            const checked = selectedIds.includes(m.id);
            return (
              <button
                key={m.id}
                onClick={() => handleCheckboxToggle(m.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                  checked
                    ? 'bg-violet-600/10 border-violet-500 text-white shadow-sm'
                    : 'bg-neutral-950/20 border-white/5 text-neutral-400 hover:text-white'
                }`}
              >
                <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-colors ${
                  checked ? 'bg-violet-600 border-violet-500' : 'border-white/20'
                }`}>
                  {checked && <div className="w-1.5 h-1.5 rounded-full bg-white animate-scaleIn" />}
                </div>
                <span className="font-mono">{m.model_name}</span>
                <span className="text-[10px] text-neutral-500 capitalize">({m.provider})</span>
              </button>
            );
          })}
        </div>
      </Card>

      {/* Prompt Editor & Run Card */}
      <Card className="p-4 flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="bg-neutral-950/40 border-white/5 text-xs h-16 placeholder-neutral-600 resize-none font-medium text-white"
            placeholder="Type prompt here..."
          />
        </div>
        <div className="flex items-center justify-end shrink-0">
          <Button
            variant="violet"
            size="sm"
            onClick={handleRunComparison}
            disabled={isRunning || selectedIds.length === 0}
            className="h-10 text-xs px-5"
          >
            <Play className="w-3.5 h-3.5 mr-1.5" />
            Run Comparison
          </Button>
        </div>
      </Card>

      {/* Side-by-Side Inferences Columns */}
      {comparisonList.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {comparisonList.map((c, i) => (
            <Card key={i} className="flex flex-col gap-4 border border-white/5 bg-neutral-950/20">
              {/* Card Header Stats */}
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white font-mono">{c.modelIdentifier}</span>
                    <Badge variant="violet" size="sm" className="capitalize text-[9px] py-0">
                      {c.provider}
                    </Badge>
                  </div>
                  <span className="text-[11px] text-neutral-400 font-sans">{c.modelName}</span>
                </div>
                <Badge variant={c.isGenerating ? 'amber' : 'emerald'} size="sm" dot>
                  {c.isGenerating ? 'Streaming' : 'Ready'}
                </Badge>
              </div>

              {/* Benchmarks Grid */}
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="p-2 rounded-lg bg-neutral-950 border border-white/5 flex items-center justify-between">
                  <span className="text-neutral-500">Latency:</span>
                  <span className="text-amber-400 font-bold">{c.latencySec ? `${c.latencySec.toFixed(2)}s` : 'Pinging'}</span>
                </div>
                <div className="p-2 rounded-lg bg-neutral-950 border border-white/5 flex items-center justify-between">
                  <span className="text-neutral-500">Tokens/s:</span>
                  <span className="text-violet-400 font-bold">{c.tokensPerSec} t/s</span>
                </div>
                <div className="p-2 rounded-lg bg-neutral-950 border border-white/5 flex items-center justify-between">
                  <span className="text-neutral-500">Cost:</span>
                  <span className="text-emerald-400 font-bold">${c.costUsd.toFixed(5)}</span>
                </div>
                <div className="p-2 rounded-lg bg-neutral-950 border border-white/5 flex items-center justify-between">
                  <span className="text-neutral-500">Tokens:</span>
                  <span className="text-neutral-300 font-bold">{c.tokensCount}</span>
                </div>
              </div>

              {/* Completion Response Text Screen */}
              <div className="flex-1 p-3.5 rounded-xl bg-black/40 border border-white/5 font-sans text-xs text-neutral-300 min-h-[300px] overflow-y-auto leading-relaxed max-h-[350px]">
                {c.response ? (
                  activeCategory === 'image' ? (
                    <div className="flex flex-col gap-2 items-center justify-center h-full">
                      <img 
                        src={c.response} 
                        alt={c.modelName} 
                        className="rounded-xl max-h-[250px] border border-white/5 object-cover w-full shadow-lg"
                      />
                      <a 
                        href={c.response} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="text-[10px] text-violet-400 hover:underline font-mono"
                      >
                        Open Original URL
                      </a>
                    </div>
                  ) : (
                    // Simple high-fidelity render helper for Markdown preview
                    <div className="flex flex-col gap-3">
                      {c.response.split('\n\n').map((para, idx) => {
                        if (para.startsWith('###')) {
                          return <h4 key={idx} className="text-white font-bold text-sm mt-1">{para.replace('###', '').trim()}</h4>;
                        }
                        if (para.startsWith('-')) {
                          return (
                            <ul key={idx} className="list-disc pl-5 flex flex-col gap-1">
                              {para.split('\n').map((li, j) => (
                                <li key={j}>{li.replace('-', '').trim()}</li>
                              ))}
                            </ul>
                          );
                        }
                        return <p key={idx}>{para}</p>;
                      })}
                    </div>
                  )
                ) : (
                  <span className="text-neutral-600 font-mono italic animate-pulse">Running model query calculations...</span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
