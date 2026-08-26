import * as React from 'react';
import { useProviders } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { 
  Cpu, CheckCircle2, AlertTriangle, Shield, RefreshCw, 
  Layers, Database, BarChart3, Sliders, ShieldCheck, Check, 
  Edit, X, Eye, EyeOff, Search, Clock, DollarSign, Activity, FileText,
  Loader2
} from 'lucide-react';
import { apiClient } from '@/services/api-client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Provider descriptions & logo maps
const PROVIDER_METADATA: Record<string, { label: string; logo: string; desc: string }> = {
  groq: { label: 'Groq API', logo: '⚡', desc: 'Ultra-low latency LPU engine powering Llama, Mixtral, and Gemma.' },
  openai: { label: 'OpenAI', logo: '🤖', desc: 'Advanced cognitive models like GPT-4o, GPT-4o-mini, and Embeddings.' },
  anthropic: { label: 'Anthropic Claude', logo: '🧬', desc: 'Highly precise context understanding and Claude 3.5 models.' },
  google: { label: 'Google Gemini', logo: '♊', desc: 'Industry-leading multimodal capabilities and massive context windows.' },
  openrouter: { label: 'OpenRouter', logo: '🌐', desc: 'Unified gateway providing access to hundreds of open weights LLMs.' },
  deepseek: { label: 'DeepSeek', logo: '🌊', desc: 'Cost-optimized deep reasoning models like DeepSeek-R1.' },
  mistral: { label: 'Mistral AI', logo: '🗼', desc: 'State of the art open-source LLMs from France.' },
  ollama: { label: 'Local Ollama', logo: '🦙', desc: 'Secure local model execution inside your network boundary.' },
  cloudflare: { label: 'Cloudflare Workers AI', logo: '☁️', desc: 'Distributed serverless AI models running on Cloudflare Edge.' },
  pollinations: { label: 'Pollinations AI', logo: '🎨', desc: 'Free default text and image model server without API credential keys.' },
  replicate: { label: 'Replicate', logo: '📦', desc: 'Cloud repository hosting open-source diffusion and video generators.' },
  together: { label: 'Together AI', logo: '🤝', desc: 'High-performance API endpoints for custom fine-tuned weights.' },
  fal: { label: 'Fal AI', logo: '🦅', desc: 'Real-time media generation for ultra-fast Flux and diffusion pipelines.' },
  stability: { label: 'Stability AI', logo: '🎯', desc: 'Creators of Stable Diffusion, Stable Video, and image models.' },
  ideogram: { label: 'Ideogram', logo: '🅰️', desc: 'Leading typography and design generation models.' },
  blackforestlabs: { label: 'Black Forest Labs', logo: '🌲', desc: 'Creators of the state-of-the-art Flux image models family.' },
};

const CAPABILITY_TABS = [
  'All', 'Text', 'Image', 'Video', 'Vision', 'Speech', 'Embeddings', 'OCR', 'Moderation', 'Multimodal'
];

export function ProvidersPage() {
  const queryClient = useQueryClient();
  const { providers, isLoading, refetch } = useProviders();

  // Active dashboard tab
  const [activeTab, setActiveTab] = React.useState<'directory' | 'logs' | 'benchmarks' | 'settings'>('directory');
  
  // Selected capability filter
  const [selectedCapability, setSelectedCapability] = React.useState<string>('All');
  
  // Search query
  const [searchQuery, setSearchQuery] = React.useState<string>('');

  // Editing provider modal state
  const [editingProvider, setEditingProvider] = React.useState<any | null>(null);
  const [showKey, setShowKey] = React.useState<boolean>(false);
  const [showSecretKey, setShowSecretKey] = React.useState<boolean>(false);

  // Health checking state per provider
  const [testingConnection, setTestingConnection] = React.useState<Record<string, boolean>>({});

  // Query: Logs
  const [logFilters, setLogFilters] = React.useState({
    provider: '',
    capability: '',
    status: '',
  });

  const { data: logs = [], isLoading: loadingLogs, refetch: refetchLogs } = useQuery<any[]>({
    queryKey: ['ai-execution-logs', logFilters],
    queryFn: async () => {
      const q = new URLSearchParams(logFilters).toString();
      const res = await apiClient.get(`/ai/providers/logs?${q}`);
      return res.data || [];
    },
    enabled: activeTab === 'logs',
  });

  // Query: Router Settings
  const { data: routerSettings, isLoading: loadingRouterSettings } = useQuery<any>({
    queryKey: ['ai-router-settings'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/router/');
      return res.data;
    },
    enabled: activeTab === 'settings',
  });

  // Mutation: Update Router Settings
  const updateRouterSettingsMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await apiClient.put('/ai/router/', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-router-settings'] });
      toast.success('Router Preferences Saved', 'Core settings updated.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.message || 'Could not update router settings.');
    }
  });

  // Mutation: Update Provider Details
  const updateProviderMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: any }) => {
      const res = await apiClient.put(`/ai/providers/${id}`, payload);
      return res.data;
    },
    onSuccess: () => {
      refetch();
      setEditingProvider(null);
      toast.success('Configuration Saved', 'Provider settings registered and encrypted at rest.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.message || 'Could not update provider details.');
    }
  });

  const handleTestConnection = async (id: string, name: string) => {
    setTestingConnection((prev) => ({ ...prev, [name]: true }));
    const toastId = toast.loading(`Triggering health check ping to ${name}...`);
    try {
      const res = await apiClient.post(`/ai/providers/${id}/health-check`);
      const data = res.data;
      if (data.is_healthy) {
        toast.dismiss(toastId);
        toast.success(`${name} is Healthy`, `Latency: ${data.latency}ms. Connection established.`);
      } else {
        toast.dismiss(toastId);
        toast.error(`${name} Offline`, `Check: ${data.error_message || 'Timeout'}`);
      }
      refetch();
    } catch (e) {
      toast.dismiss(toastId);
      toast.error('Ping Failed', 'Central network timeout or API credentials invalid.');
    } finally {
      setTestingConnection((prev) => ({ ...prev, [name]: false }));
    }
  };

  const handleSyncAll = async () => {
    toast.loading('Syncing gateway provider statuses...');
    await refetch();
    toast.dismiss();
    toast.success('Sync Complete', 'Central gateway state synchronized.');
  };

  // Filter provider list dynamically
  const filteredProviders = React.useMemo(() => {
    return providers.filter((p: any) => {
      // Capability filter
      if (selectedCapability !== 'All') {
        const caps = p.supported_capabilities || [];
        const matches = caps.some((c: string) => c.toLowerCase() === selectedCapability.toLowerCase());
        if (!matches) return false;
      }
      // Search query filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return p.name.toLowerCase().includes(query) || p.supported_models.some((m: string) => m.toLowerCase().includes(query));
      }
      return true;
    });
  }, [providers, selectedCapability, searchQuery]);

  // Aggregate stats
  const totalCount = providers.length;
  const healthyCount = providers.filter((p: any) => p.status === 'Healthy').length;
  const offlineCount = totalCount - healthyCount;
  const totalCost = providers.reduce((sum: number, p: any) => sum + (p.usage?.last_30_days?.cost || 0), 0);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12 px-4 text-white">
      {/* Header */}
      <PageHeader
        title="Enterprise AI Provider Platform"
        description="Centralized credentials management, dynamic capabilities registry, health telemetry checks, and automatic fallback routing rules."
        icon={<Cpu className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">{providers.length} Connected</Badge>}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncAll}
            disabled={isLoading}
            className="h-9 gap-1.5 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Sync Gateway State
          </Button>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass rounded-2xl p-5 flex flex-col gap-1.5 border border-white/5 relative overflow-hidden bg-neutral-950/20">
          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-violet-400" /> Active Registry
          </span>
          <span className="text-2xl font-bold font-mono">{totalCount} Channels</span>
          <p className="text-[10px] text-neutral-500">Dynamically loaded providers</p>
        </div>

        <div className="glass rounded-2xl p-5 flex flex-col gap-1.5 border border-white/5 relative overflow-hidden bg-neutral-950/20">
          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Healthy Nodes
          </span>
          <span className="text-2xl font-bold font-mono text-emerald-400">
            {healthyCount} Active
          </span>
          <p className="text-[10px] text-neutral-500">
            Passing auto-pings ({totalCount ? Math.round((healthyCount / totalCount) * 100) : 0}%)
          </p>
        </div>

        <div className="glass rounded-2xl p-5 flex flex-col gap-1.5 border border-white/5 relative overflow-hidden bg-neutral-950/20">
          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-rose-400" /> Degraded / Offline
          </span>
          <span className="text-2xl font-bold font-mono text-rose-400">
            {offlineCount} Down
          </span>
          <p className="text-[10px] text-neutral-500">Automatically bypassed in routing</p>
        </div>

        <div className="glass rounded-2xl p-5 flex flex-col gap-1.5 border border-white/5 relative overflow-hidden bg-neutral-950/20">
          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-amber-400" /> 30d Platform Spend
          </span>
          <span className="text-2xl font-bold font-mono text-amber-400">
            ${totalCost.toFixed(4)}
          </span>
          <p className="text-[10px] text-neutral-500">Accumulated tokens execution cost</p>
        </div>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-white/5 gap-2">
        <Button
          variant="ghost"
          onClick={() => setActiveTab('directory')}
          className={`px-4 py-2 text-xs border-b-2 rounded-none hover:bg-transparent ${
            activeTab === 'directory' 
              ? 'border-violet-500 text-violet-400 font-bold' 
              : 'border-transparent text-neutral-400'
          }`}
        >
          <Layers className="w-3.5 h-3.5 mr-1.5" /> Providers Directory
        </Button>
        <Button
          variant="ghost"
          onClick={() => setActiveTab('logs')}
          className={`px-4 py-2 text-xs border-b-2 rounded-none hover:bg-transparent ${
            activeTab === 'logs' 
              ? 'border-violet-500 text-violet-400 font-bold' 
              : 'border-transparent text-neutral-400'
          }`}
        >
          <FileText className="w-3.5 h-3.5 mr-1.5" /> Execution Audit Logs
        </Button>
        <Button
          variant="ghost"
          onClick={() => setActiveTab('benchmarks')}
          className={`px-4 py-2 text-xs border-b-2 rounded-none hover:bg-transparent ${
            activeTab === 'benchmarks' 
              ? 'border-violet-500 text-violet-400 font-bold' 
              : 'border-transparent text-neutral-400'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5 mr-1.5" /> Reliability Benchmarks
        </Button>
        <Button
          variant="ghost"
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 text-xs border-b-2 rounded-none hover:bg-transparent ${
            activeTab === 'settings' 
              ? 'border-violet-500 text-violet-400 font-bold' 
              : 'border-transparent text-neutral-400'
          }`}
        >
          <Sliders className="w-3.5 h-3.5 mr-1.5" /> Routing Engine Config
        </Button>
      </div>

      {/* TAB CONTENTS: DIRECTORY */}
      {activeTab === 'directory' && (
        <div className="flex flex-col gap-6">
          {/* Controls Panel */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-neutral-950/20 border border-white/5 rounded-2xl p-4">
            {/* Capability Filtering */}
            <div className="flex flex-wrap gap-1">
              {CAPABILITY_TABS.map((tab) => (
                <Button
                  key={tab}
                  size="sm"
                  onClick={() => setSelectedCapability(tab)}
                  className={`text-[11px] h-8 px-3 rounded-lg ${
                    selectedCapability === tab 
                      ? 'bg-violet-600 text-white font-bold' 
                      : 'bg-neutral-900 border border-white/5 text-neutral-400 hover:text-white'
                  }`}
                >
                  {tab}
                </Button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-neutral-500" />
              <Input
                placeholder="Search by name, key, or model..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-neutral-900 border-white/5 text-xs h-9"
              />
            </div>
          </div>

          {/* Providers Cards Grid */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-72 rounded-2xl border border-white/5 bg-neutral-900/20 animate-pulse" />
              ))}
            </div>
          ) : filteredProviders.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProviders.map((p: any) => {
                const meta = {
                  label: p.label || PROVIDER_METADATA[p.name.toLowerCase()]?.label || p.name,
                  logo: p.logo || PROVIDER_METADATA[p.name.toLowerCase()]?.logo || '🔗',
                  desc: p.description || PROVIDER_METADATA[p.name.toLowerCase()]?.desc || 'Enterprise AI Provider Integration',
                };
                return (
                  <div 
                    key={p.id}
                    className={`glass rounded-2xl p-5 border flex flex-col gap-4 transition-all duration-300 relative group bg-neutral-950/20 hover:border-violet-500/20`}
                  >
                    {/* Top Row */}
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-3">
                        <div className="text-2xl w-10 h-10 rounded-xl bg-neutral-900 border border-white/5 flex items-center justify-center">
                          {meta.logo}
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <h3 className="font-bold text-white text-sm">{meta.label}</h3>
                            {p.is_default && (
                              <Badge variant="violet" className="text-[9px] px-1 py-0 h-4">Default</Badge>
                            )}
                          </div>
                          <span className="text-[10px] text-neutral-400 font-mono">{p.name} gateway</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge variant={p.status === 'Healthy' ? 'emerald' : 'rose'} className="text-[9px]">
                          {p.status}
                        </Badge>
                        <Badge variant={p.is_active ? 'violet' : 'neutral'} className="text-[9px]">
                          {p.is_active ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </div>
                    </div>

                    {/* Desc */}
                    <p className="text-[11px] text-neutral-400 leading-relaxed min-h-[32px]">{meta.desc || 'No provider details registered.'}</p>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-3 gap-2 bg-neutral-950/40 border border-white/5 rounded-xl p-2.5">
                      <div className="flex flex-col">
                        <span className="text-[8px] text-neutral-500 uppercase font-bold">Latency</span>
                        <span className="text-xs font-mono font-bold text-neutral-200">{p.latency}ms</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[8px] text-neutral-500 uppercase font-bold">Success</span>
                        <span className="text-xs font-mono font-bold text-emerald-400">{p.success_rate.toFixed(1)}%</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[8px] text-neutral-500 uppercase font-bold">Priority</span>
                        <span className="text-xs font-mono font-bold text-neutral-200">#{p.priority}</span>
                      </div>
                    </div>

                    {/* Capabilities & Default Badges */}
                    <div className="flex flex-col gap-1.5">
                      <span className="text-[9px] text-neutral-500 font-bold uppercase">Capabilities</span>
                      <div className="flex flex-wrap gap-1">
                        {p.supported_capabilities?.map((cap: string) => (
                          <Badge key={cap} variant="neutral" className="text-[9px] bg-neutral-900 border-white/5 py-0">
                            {cap}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Supported Models */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] text-neutral-500 font-bold uppercase">Models ({p.supported_models?.length || 0})</span>
                      <div className="text-[10px] text-neutral-400 truncate max-w-full font-mono bg-neutral-950/30 p-1.5 rounded-lg border border-white/5">
                        {p.supported_models?.join(', ') || 'No registered models.'}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-1.5 border-t border-white/5 pt-3 mt-auto">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingProvider(p)}
                        className="text-[11px] h-8 px-2.5 border-white/5 bg-neutral-900 hover:bg-neutral-800 text-neutral-300"
                      >
                        <Edit className="w-3 h-3 mr-1" /> Configure
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTestConnection(p.id, p.name)}
                        className="flex-1 text-[11px] h-8 border-white/5 bg-neutral-900 hover:bg-neutral-800"
                        disabled={testingConnection[p.name]}
                      >
                        <RefreshCw className={`w-3 h-3 mr-1 ${testingConnection[p.name] ? 'animate-spin' : ''}`} />
                        Test Health
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const action = p.is_active ? 'Disable' : 'Enable';
                          updateProviderMutation.mutate({
                            id: p.id,
                            payload: { is_active: !p.is_active }
                          });
                        }}
                        className={`text-[11px] h-8 px-3 border-white/5 ${
                          p.is_active 
                            ? 'text-rose-400 hover:bg-rose-500/10' 
                            : 'text-emerald-400 hover:bg-emerald-500/10'
                        }`}
                      >
                        {p.is_active ? 'Disable' : 'Enable'}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-center py-20 border border-dashed border-white/5 rounded-2xl bg-neutral-950/20">
              <Cpu className="w-8 h-8 text-neutral-600 mb-3" />
              <h3 className="font-bold text-white text-sm">No Channels Found</h3>
              <p className="text-xs text-neutral-500 max-w-xs mt-1">
                There are no dynamic providers matching your active filters.
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENTS: EXECUTION LOGS */}
      {activeTab === 'logs' && (
        <div className="flex flex-col gap-4 bg-neutral-950/20 border border-white/5 rounded-2xl p-6">
          {/* Logs Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase">Provider Filter</label>
              <Select
                value={logFilters.provider}
                onChange={(e) => setLogFilters(prev => ({ ...prev, provider: e.target.value }))}
                className="bg-neutral-900 border-white/5 text-xs h-9"
                options={[
                  { label: 'All Providers', value: '' },
                  ...providers.map((p: any) => ({ label: p.name, value: p.name }))
                ]}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase">Capability Filter</label>
              <Select
                value={logFilters.capability}
                onChange={(e) => setLogFilters(prev => ({ ...prev, capability: e.target.value }))}
                className="bg-neutral-900 border-white/5 text-xs h-9"
                options={[
                  { label: 'All Capabilities', value: '' },
                  { label: 'Text Generation', value: 'text' },
                  { label: 'Image Generation', value: 'image' },
                  { label: 'Vision Processing', value: 'vision' },
                  { label: 'Speech-to-Text', value: 'speech' },
                  { label: 'Embeddings', value: 'embeddings' }
                ]}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase">Status Filter</label>
              <Select
                value={logFilters.status}
                onChange={(e) => setLogFilters(prev => ({ ...prev, status: e.target.value }))}
                className="bg-neutral-900 border-white/5 text-xs h-9"
                options={[
                  { label: 'All Statuses', value: '' },
                  { label: 'Success', value: 'success' },
                  { label: 'Failure', value: 'failure' }
                ]}
              />
            </div>

            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => refetchLogs()}
                disabled={loadingLogs}
                className="w-full bg-neutral-900 hover:bg-neutral-800 border-white/5 text-xs h-9"
              >
                <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loadingLogs ? 'animate-spin' : ''}`} />
                Refresh Logs
              </Button>
            </div>
          </div>

          {/* Logs Table */}
          {loadingLogs ? (
            <div className="flex flex-col gap-2 py-10 items-center justify-center text-neutral-500 text-xs">
              <Loader2 className="w-5 h-5 animate-spin text-violet-500" />
              Retrieving execution audit trace...
            </div>
          ) : logs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-neutral-400 bg-neutral-950/40">
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Provider</th>
                    <th className="p-3">Model</th>
                    <th className="p-3">Capability</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">Cost (USD)</th>
                    <th className="p-3">Retries</th>
                    <th className="p-3">Agent</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((l: any) => (
                    <tr key={l.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="p-3 font-mono text-neutral-400 text-[10px]">
                        {new Date(l.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="p-3 font-semibold capitalize">{l.provider}</td>
                      <td className="p-3 font-mono text-[10px] text-neutral-300 max-w-[120px] truncate">{l.model}</td>
                      <td className="p-3 capitalize">{l.capability}</td>
                      <td className="p-3 font-mono">{l.latency}ms</td>
                      <td className="p-3 font-mono text-emerald-400">${l.cost.toFixed(5)}</td>
                      <td className="p-3 font-mono text-neutral-400">{l.retry_count}</td>
                      <td className="p-3 font-mono text-neutral-400 capitalize">{l.agent}</td>
                      <td className="p-3">
                        <Badge variant={l.status === 'success' ? 'emerald' : 'rose'} size="sm">
                          {l.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-neutral-500 text-xs border border-dashed border-white/5 rounded-xl">
              No recent logs matching filter criteria found in the active workspace.
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENTS: BENCHMARKS */}
      {activeTab === 'benchmarks' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass rounded-2xl p-6 border border-white/5 bg-neutral-950/20">
            <h3 className="font-bold text-white text-sm mb-4">Availability Rates</h3>
            <div className="space-y-4">
              {providers.map((p: any) => (
                <div key={p.id} className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold">{p.name}</span>
                    <span className="font-mono text-emerald-400 font-bold">{p.success_rate.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-neutral-900 rounded-full h-2 border border-white/5">
                    <div 
                      className={`h-2 rounded-full ${p.success_rate > 95 ? 'bg-emerald-500' : p.success_rate > 80 ? 'bg-amber-500' : 'bg-rose-500'}`}
                      style={{ width: `${p.success_rate}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-2xl p-6 border border-white/5 bg-neutral-950/20">
            <h3 className="font-bold text-white text-sm mb-4">Average Ping Latency</h3>
            <div className="space-y-4">
              {providers.map((p: any) => (
                <div key={p.id} className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold">{p.name}</span>
                    <span className="font-mono text-neutral-300">{p.latency}ms</span>
                  </div>
                  <div className="w-full bg-neutral-900 rounded-full h-2 border border-white/5">
                    <div 
                      className="h-2 rounded-full bg-violet-500"
                      style={{ width: `${Math.min(100, (p.latency / 1200) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENTS: ROUTING ENGINE */}
      {activeTab === 'settings' && (
        <div className="glass rounded-2xl p-6 border border-white/5 bg-neutral-950/20 max-w-3xl flex flex-col gap-6">
          <div>
            <h3 className="font-bold text-white text-sm">Router Core Configuration</h3>
            <p className="text-[11px] text-neutral-500">Configure global fallback, strategies, and default providers per category.</p>
          </div>

          {loadingRouterSettings ? (
            <div className="flex py-10 items-center justify-center text-neutral-500 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-violet-400 mr-2" /> Loading configuration...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Routing Strategy Mode</label>
                <Select
                  value={routerSettings?.routing_mode || 'cheapest'}
                  onChange={(e) => updateRouterSettingsMutation.mutate({ ...routerSettings, routing_mode: e.target.value })}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={[
                    { label: 'Cheapest (Cost optimized)', value: 'cheapest' },
                    { label: 'Fastest (Latency optimized)', value: 'fastest' },
                    { label: 'Highest Quality (Priority-based)', value: 'highest_quality' },
                    { label: 'Balanced (Weighted speed/cost)', value: 'balanced' },
                  ]}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Global Fallback Provider</label>
                <Select
                  value={routerSettings?.fallback_provider || 'groq'}
                  onChange={(e) => updateRouterSettingsMutation.mutate({ ...routerSettings, fallback_provider: e.target.value })}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={providers.map((p: any) => ({ label: p.name, value: p.name }))}
                />
              </div>

              {/* Capability defaults */}
              <div className="md:col-span-2 border-t border-white/5 pt-4 mt-2">
                <h4 className="text-xs font-bold text-neutral-300 uppercase tracking-wider mb-3">Capability Default Providers</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-neutral-400 font-semibold">Default Text Provider</label>
                    <Select
                      value={routerSettings?.default_text_provider || 'openai'}
                      onChange={(e) => updateRouterSettingsMutation.mutate({ ...routerSettings, default_text_provider: e.target.value })}
                      className="bg-neutral-900 border-white/5 h-9 text-xs"
                      options={providers.map((p: any) => ({ label: p.name, value: p.name }))}
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-neutral-400 font-semibold">Default Image Provider</label>
                    <Select
                      value={routerSettings?.default_image_provider || 'pollinations'}
                      onChange={(e) => updateRouterSettingsMutation.mutate({ ...routerSettings, default_image_provider: e.target.value })}
                      className="bg-neutral-900 border-white/5 h-9 text-xs"
                      options={providers.map((p: any) => ({ label: p.name, value: p.name }))}
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-neutral-400 font-semibold">Default Video Provider</label>
                    <Select
                      value={routerSettings?.default_video_provider || 'pollinations'}
                      onChange={(e) => updateRouterSettingsMutation.mutate({ ...routerSettings, default_video_provider: e.target.value })}
                      className="bg-neutral-900 border-white/5 h-9 text-xs"
                      options={providers.map((p: any) => ({ label: p.name, value: p.name }))}
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-neutral-400 font-semibold">Default Vision Provider</label>
                    <Select
                      value={routerSettings?.default_vision_provider || 'google'}
                      onChange={(e) => updateRouterSettingsMutation.mutate({ ...routerSettings, default_vision_provider: e.target.value })}
                      className="bg-neutral-900 border-white/5 h-9 text-xs"
                      options={providers.map((p: any) => ({ label: p.name, value: p.name }))}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* DIALOG EDIT CONFIGURATION MODAL */}
      {editingProvider && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass bg-neutral-950 border border-white/10 rounded-2xl p-6 w-full max-w-xl flex flex-col gap-4 text-white relative shadow-2xl">
            {/* Close */}
            <button 
              onClick={() => setEditingProvider(null)}
              className="absolute right-4 top-4 p-1.5 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Header */}
            <div>
              <h3 className="font-bold text-white text-base">Configure {editingProvider.name} Parameters</h3>
              <p className="text-[11px] text-neutral-400 mt-0.5">Secure organization-wide keys and endpoint overrides.</p>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-[70vh] overflow-y-auto pr-1">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Status Channel</label>
                <Select
                  value={editingProvider.is_active ? 'active' : 'inactive'}
                  onChange={(e) => setEditingProvider((prev: any) => ({ ...prev, is_active: e.target.value === 'active' }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                  options={[
                    { label: 'Active / Healthy Routing', value: 'active' },
                    { label: 'Suspended / Disabled', value: 'inactive' }
                  ]}
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Priority rank</label>
                <Input
                  type="number"
                  value={editingProvider.priority}
                  onChange={(e) => setEditingProvider((prev: any) => ({ ...prev, priority: parseInt(e.target.value) || 1 }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              {/* API Key */}
              <div className="flex flex-col gap-1 sm:col-span-2 relative">
                <label className="text-xs text-neutral-400 font-semibold">API key (Encrypted)</label>
                <div className="relative">
                  <Input
                    type={showKey ? 'text' : 'password'}
                    placeholder={editingProvider.config?.api_key ? '••••••••••••••••••••' : 'Enter key...'}
                    value={editingProvider.config?.api_key || ''}
                    onChange={(e) => setEditingProvider((prev: any) => ({
                      ...prev,
                      config: { ...prev.config, api_key: e.target.value }
                    }))}
                    className="bg-neutral-900 border-white/5 text-xs h-9 pr-10"
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-2.5 p-0.5 rounded-lg text-neutral-500 hover:text-white"
                  >
                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Secret Key */}
              <div className="flex flex-col gap-1 sm:col-span-2 relative">
                <label className="text-xs text-neutral-400 font-semibold">Secret Key (Encrypted, optional)</label>
                <div className="relative">
                  <Input
                    type={showSecretKey ? 'text' : 'password'}
                    placeholder={editingProvider.config?.secret_key ? '••••••••••••••••••••' : 'Enter secret key...'}
                    value={editingProvider.config?.secret_key || ''}
                    onChange={(e) => setEditingProvider((prev: any) => ({
                      ...prev,
                      config: { ...prev.config, secret_key: e.target.value }
                    }))}
                    className="bg-neutral-900 border-white/5 text-xs h-9 pr-10"
                  />
                  <button
                    onClick={() => setShowSecretKey(!showSecretKey)}
                    className="absolute right-3 top-2.5 p-0.5 rounded-lg text-neutral-500 hover:text-white"
                  >
                    {showSecretKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Account ID (optional)</label>
                <Input
                  value={editingProvider.config?.account_id || ''}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, account_id: e.target.value }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Organization ID (optional)</label>
                <Input
                  value={editingProvider.config?.organization_id_val || ''}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, organization_id_val: e.target.value }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              <div className="flex flex-col gap-1 sm:col-span-2">
                <label className="text-xs text-neutral-400 font-semibold">Endpoint URL override (optional)</label>
                <Input
                  value={editingProvider.config?.endpoint_url || ''}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, endpoint_url: e.target.value }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Region (optional)</label>
                <Input
                  value={editingProvider.config?.region || ''}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, region: e.target.value }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Custom Endpoint</label>
                <Select
                  value={editingProvider.config?.custom_endpoint ? 'true' : 'false'}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, custom_endpoint: e.target.value === 'true' }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                  options={[
                    { label: 'Standard API Endpoint', value: 'false' },
                    { label: 'Custom Domain Endpoint', value: 'true' }
                  ]}
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Timeout (seconds)</label>
                <Input
                  type="number"
                  value={editingProvider.config?.timeout || 30}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, timeout: parseInt(e.target.value) || 30 }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Retry count limit</label>
                <Input
                  type="number"
                  value={editingProvider.config?.retry_count || 3}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, retry_count: parseInt(e.target.value) || 3 }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Rate Limits</label>
                <Input
                  placeholder="e.g. 60 RPM"
                  value={editingProvider.config?.rate_limits || ''}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, rate_limits: e.target.value }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-neutral-400 font-semibold">Health check toggle</label>
                <Select
                  value={editingProvider.config?.health_check_enabled !== false ? 'true' : 'false'}
                  onChange={(e) => setEditingProvider((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, health_check_enabled: e.target.value === 'true' }
                  }))}
                  className="bg-neutral-900 border-white/5 text-xs h-9"
                  options={[
                    { label: 'Health checking enabled', value: 'true' },
                    { label: 'Bypass checks', value: 'false' }
                  ]}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-2 border-t border-white/5 pt-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingProvider(null)}
                className="text-xs h-9 border border-white/5 hover:bg-neutral-900 text-neutral-400 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                variant="violet"
                size="sm"
                onClick={() => {
                  updateProviderMutation.mutate({
                    id: editingProvider.id,
                    payload: {
                      is_active: editingProvider.is_active,
                      priority: editingProvider.priority,
                      config: editingProvider.config
                    }
                  });
                }}
                disabled={updateProviderMutation.isPending}
                className="text-xs h-9 gap-1.5"
              >
                {updateProviderMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
                Apply Configuration
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
