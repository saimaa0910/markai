import * as React from 'react';
import { useModels } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { Input, Select } from '@/components/ui/input';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, Database, Star, Play, Settings2, ShieldCheck, 
  ShieldAlert, Sparkles, Code, BrainCircuit, Activity, DollarSign, Plus, X 
} from 'lucide-react';
import { 
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid 
} from 'recharts';
import { useAIPlatformStore } from '../store/ai-platform';
import { toast } from '@/components/ui/toast';

interface ModelDetailsPageProps {
  id: string;
}

interface BenchmarkData {
  mmlu: number;
  humanEval: number;
  math: number;
  reasoning: number;
}

const STATIC_BENCHMARKS: Record<string, BenchmarkData> = {
  'llama3-70b-8192': { mmlu: 82, humanEval: 81, math: 50, reasoning: 78 },
  'llama3-8b-8192': { mmlu: 68, humanEval: 62, math: 32, reasoning: 58 },
  'gpt-4o-mini': { mmlu: 82, humanEval: 87, math: 70, reasoning: 80 },
  'gpt-4o': { mmlu: 88, humanEval: 90, math: 76, reasoning: 92 },
  'claude-3-5-sonnet-20240620': { mmlu: 88, humanEval: 92, math: 78, reasoning: 94 },
  'gemini-1.5-flash': { mmlu: 78, humanEval: 74, math: 48, reasoning: 72 },
  'text-embedding-3-small': { mmlu: 0, humanEval: 0, math: 0, reasoning: 0 },
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-white/10 rounded-lg p-2.5 shadow-xl text-xs font-mono">
      <p className="text-neutral-500 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <span style={{ color: p.color }}>●</span>
          <span className="text-neutral-300">{p.name}:</span>
          <span className="font-bold text-white">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export function ModelDetailsPage({ id }: ModelDetailsPageProps) {
  const { models, isLoading, refetch, toggleHealth } = useModels();
  const { favorites, toggleFavorite } = useAIPlatformStore();

  const [activeTab, setActiveTab] = React.useState<'benchmarks' | 'specs' | 'tags'>('benchmarks');
  const [modelCategory, setModelCategory] = React.useState('chat');
  const [tagInput, setTagInput] = React.useState('');
  
  // Custom tag list stored in local state
  const [modelTags, setModelTags] = React.useState<string[]>(['production-safe', 'reasoning']);

  const model = React.useMemo(() => {
    return models.find((m) => m.id === id || m.model_name === id);
  }, [models, id]);

  const isFavorite = React.useMemo(() => {
    return model ? favorites.includes(model.id) : false;
  }, [favorites, model]);

  const handleToggleFavorite = () => {
    if (!model) return;
    toggleFavorite(model.id);
    toast.success(
      isFavorite ? 'Removed Favorite' : 'Marked Favorite',
      `${model.name} health star status has been modified.`
    );
  };

  const handleAddTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (!tagInput.trim()) return;
    if (modelTags.includes(tagInput.trim().toLowerCase())) {
      toast.error('Duplicate Tag', 'Tag already exists.');
      return;
    }
    setModelTags([...modelTags, tagInput.trim().toLowerCase()]);
    setTagInput('');
    toast.success('Tag Added', 'Model metadata tags updated.');
  };

  const handleRemoveTag = (tag: string) => {
    setModelTags(modelTags.filter((t) => t !== tag));
    toast.success('Tag Removed', 'Model metadata tags updated.');
  };

  const benchmarks = React.useMemo(() => {
    if (!model) return { mmlu: 0, humanEval: 0, math: 0, reasoning: 0 };
    return STATIC_BENCHMARKS[model.model_name] || { mmlu: 75, humanEval: 70, math: 45, reasoning: 70 };
  }, [model]);

  const radarData = [
    { subject: 'MMLU Academic', A: benchmarks.mmlu, fullMark: 100 },
    { subject: 'HumanEval Coding', A: benchmarks.humanEval, fullMark: 100 },
    { subject: 'Math Reasoning', A: benchmarks.math, fullMark: 100 },
    { subject: 'Logical Depth', A: benchmarks.reasoning, fullMark: 100 },
  ];

  if (isLoading && !model) {
    return (
      <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12 animate-pulse">
        <div className="h-20 bg-neutral-900/60 rounded-xl border border-white/5" />
        <div className="grid grid-cols-4 gap-4 h-24 bg-neutral-900/30 rounded-xl" />
      </div>
    );
  }

  if (!model) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-4">
        <Database className="w-10 h-10 text-neutral-600" />
        <h3 className="text-white font-bold">Model Not Found</h3>
        <p className="text-xs text-neutral-500 max-w-xs">The model does not exist or has been removed from registry database.</p>
        <a href="/dashboard/ai/models">
          <Button variant="outline" size="sm" className="border-white/5">Back to Registry</Button>
        </a>
      </div>
    );
  }

  // Count capabilities
  const capCount = [
    model.supports_streaming,
    model.supports_vision,
    model.supports_json,
    model.supports_tool_calling,
    model.supports_embeddings,
    model.supports_images,
  ].filter(Boolean).length;

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Back button header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <a 
          href="/dashboard/ai/models" 
          className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Models Registry
        </a>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleFavorite}
            className={`h-8 text-[11px] border-white/5 ${isFavorite ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : ''}`}
          >
            <Star className={`w-3 h-3 mr-1 ${isFavorite ? 'fill-amber-400 text-amber-400' : ''}`} />
            {isFavorite ? 'Starred' : 'Star Model'}
          </Button>
          
          <Button
            variant="violet"
            size="sm"
            onClick={() => window.location.href = `/dashboard/ai/playground?model=${model.model_name}`}
            className="h-8 text-[11px]"
          >
            <Play className="w-3 h-3 mr-1" />
            Launch Playground
          </Button>
        </div>
      </div>

      <PageHeader
        title={model.name}
        description={`Configure tags, inspect pricing, and view benchmark indexes for ${model.model_name}.`}
        icon={<Database className="w-5 h-5 text-violet-400" />}
        badge={
          <Badge variant={model.is_healthy ? 'emerald' : 'rose'} dot>
            {model.is_healthy ? 'Healthy registry status' : 'Degraded registry status'}
          </Badge>
        }
      />

      {/* KPI metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Context Window Size"
          value={`${(model.context_window / 1000).toFixed(0)}k t`}
          icon={<BrainCircuit className="w-4 h-4 text-violet-400" />}
          description="Maximum prompt context size"
        />
        <StatCard
          title="Avg Inference Latency"
          value={`${Number(model.latency).toFixed(2)}s`}
          icon={<Activity className="w-4 h-4 text-amber-400" />}
          description="Average response overhead"
        />
        <StatCard
          title="Prompt Input Price"
          value={`$${Number(model.input_token_price).toFixed(3)}`}
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          description="Pricing per 1k input tokens"
        />
        <StatCard
          title="Inference Capabilities"
          value={`${capCount} / 6`}
          icon={<Sparkles className="w-4 h-4 text-sky-400" />}
          description="Registered model capabilities"
        />
      </div>

      {/* Tab Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation Tab Menu */}
        <div className="flex flex-col gap-2">
          {[
            { id: 'benchmarks', label: 'Inference Benchmarks' },
            { id: 'specs', label: 'Technical Specs & Caps' },
            { id: 'tags', label: 'Categories & Metadata' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2.5 rounded-xl border text-xs font-semibold text-left transition-all ${
                activeTab === tab.id
                  ? 'bg-violet-600 border-violet-500/30 text-white shadow-lg'
                  : 'bg-neutral-950/20 border-white/5 text-neutral-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab contents */}
        <div className="lg:col-span-3">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === 'benchmarks' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Benchmarks Radar */}
                  <Card className="flex flex-col gap-4">
                    <div>
                      <h3 className="font-bold text-white text-sm">Standardized Reasoning Benchmarks</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Radar comparison of logically complex metrics.</p>
                    </div>

                    <div className="h-[200px] w-full mt-2 flex items-center justify-center">
                      {benchmarks.mmlu > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                            <PolarGrid stroke="rgba(255,255,255,0.05)" />
                            <PolarAngleAxis dataKey="subject" stroke="#a3a3a3" fontSize={9} />
                            <PolarRadiusAxis stroke="#525252" fontSize={8} />
                            <Radar name="Model benchmarks" dataKey="A" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.25} />
                          </RadarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="text-xs text-neutral-600">Benchmarks unavailable for vector nodes</div>
                      )}
                    </div>
                  </Card>

                  {/* Pricing Comparison */}
                  <Card className="flex flex-col gap-4">
                    <div>
                      <h3 className="font-bold text-white text-sm">Pricing Details & Ratios</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Detailed input/output cost structures.</p>
                    </div>

                    <div className="flex flex-col gap-3 mt-2">
                      <div className="p-3 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs">
                        <span className="text-neutral-400 font-semibold">Cost per 1k input tokens:</span>
                        <span className="font-mono text-white font-bold">${Number(model.input_token_price).toFixed(4)}</span>
                      </div>

                      <div className="p-3 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs">
                        <span className="text-neutral-400 font-semibold">Cost per 1k output tokens:</span>
                        <span className="font-mono text-white font-bold">${Number(model.output_token_price).toFixed(4)}</span>
                      </div>

                      <div className="p-3 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs">
                        <span className="text-neutral-400 font-semibold">Price Ratio (Out/In):</span>
                        <span className="font-mono text-violet-400 font-bold">
                          {model.input_token_price > 0 
                            ? `${(model.output_token_price / model.input_token_price).toFixed(1)}x` 
                            : '0x'}
                        </span>
                      </div>
                    </div>
                  </Card>
                </div>
              )}

              {activeTab === 'specs' && (
                <Card className="flex flex-col gap-6">
                  <div>
                    <h3 className="font-bold text-white text-sm">Capability Checklist & Window Stats</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Full validation specifications matching active API parameters.</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Progress context window */}
                    <div className="flex flex-col gap-3">
                      <div className="flex flex-col gap-1.5">
                        <div className="flex justify-between text-xs text-neutral-300">
                          <span className="font-bold">Context Token Budget</span>
                          <span className="font-mono text-neutral-500">{Number(model.context_window).toLocaleString()} tokens</span>
                        </div>
                        <div className="w-full h-2.5 rounded-full bg-neutral-900 border border-white/5 overflow-hidden">
                          <div 
                            className="h-full bg-violet-600 rounded-full" 
                            style={{ width: `${Math.min(100, (model.context_window / 200000) * 100)}%` }} 
                          />
                        </div>
                      </div>
                    </div>

                    {/* Specifications List */}
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { label: 'Streaming Response', val: model.supports_streaming },
                        { label: 'Multimodal Vision', val: model.supports_vision },
                        { label: 'Structured JSON', val: model.supports_json },
                        { label: 'Tool/Function Calls', val: model.supports_tool_calling },
                        { label: 'Vector Embeddings', val: model.supports_embeddings },
                        { label: 'Audio Pipelines', val: model.supports_audio },
                      ].map((spec, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs">
                          {spec.val ? (
                            <ShieldCheck className="w-4.5 h-4.5 text-emerald-400 shrink-0" />
                          ) : (
                            <ShieldAlert className="w-4.5 h-4.5 text-neutral-600 shrink-0" />
                          )}
                          <span className={spec.val ? 'text-neutral-200' : 'text-neutral-500 line-through'}>
                            {spec.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              )}

              {activeTab === 'tags' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Category select */}
                  <Card className="flex flex-col gap-4">
                    <div>
                      <h3 className="font-bold text-white text-sm">Model Categorization</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Assign a functional group scope for routing priorities.</p>
                    </div>

                    <div className="flex flex-col gap-2 mt-2">
                      <Select
                        value={modelCategory}
                        onChange={(e) => {
                          setModelCategory(e.target.value);
                          toast.success('Category Configured', 'Model dynamic group saved.');
                        }}
                        className="bg-neutral-900 border-white/5 h-9 text-xs"
                        options={[
                          { label: 'General Chat / Conversation', value: 'chat' },
                          { label: 'Advanced Coding Assistant', value: 'code' },
                          { label: 'Multimodal Image Inspector', value: 'vision' },
                          { label: 'High Precision Embeddings', value: 'embeddings' },
                        ]}
                      />
                    </div>
                  </Card>

                  {/* Metadata Tags */}
                  <Card className="flex flex-col gap-4">
                    <div>
                      <h3 className="font-bold text-white text-sm">Platform Metadata Tags</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Search tags used for console indexing.</p>
                    </div>

                    {/* Tag list */}
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {modelTags.map((tag) => (
                        <Badge key={tag} variant="neutral" className="gap-1 text-[10px] pl-2 font-mono" size="sm">
                          {tag}
                          <button 
                            type="button" 
                            onClick={() => handleRemoveTag(tag)}
                            className="text-neutral-500 hover:text-white transition-colors cursor-pointer"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>

                    {/* Tag form */}
                    <form onSubmit={handleAddTag} className="flex gap-2 mt-2">
                      <Input
                        placeholder="Add new tag..."
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        className="bg-neutral-950/40 border-white/5 h-8 text-[11px]"
                      />
                      <Button
                        type="submit"
                        variant="outline"
                        size="sm"
                        className="h-8 text-[11px] border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </Button>
                    </form>
                  </Card>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
