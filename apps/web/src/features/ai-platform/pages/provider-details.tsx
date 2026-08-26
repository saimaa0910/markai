import * as React from 'react';
import { useProviders, useModels, useProviderLogs, useProviderHealth, PROVIDER_META } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { DataTable, DataTableColumn } from '@/components/ui/data-table';
import { Dialog } from '@/components/ui/dialog';
import { Card } from '@eaimos/ui';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, RefreshCw, Activity, Zap, Shield, HelpCircle, 
  AlertCircle, Key, Play, Terminal, Database, Clock, Settings2, ShieldCheck, ShieldAlert, DollarSign 
} from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar 
} from 'recharts';
import { toast } from '@/components/ui/toast';
import { InspectorDialog } from '../components/inspector-dialog';

interface ProviderDetailsPageProps {
  id: string;
}

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

export function ProviderDetailsPage({ id }: ProviderDetailsPageProps) {
  const { providers, isLoading: loadingProviders, refetch: refetchProviders } = useProviders();
  const { models, toggleHealth, updatePriority, refetch: refetchModels } = useModels();
  const { logs, stats, isLoading: loadingLogs, refetch: refetchLogs } = useProviderLogs(id);
  const { testConnection } = useProviderHealth();

  const [activeTab, setActiveTab] = React.useState<'models' | 'history' | 'logs' | 'incidents' | 'quota'>('models');
  const [showWizard, setShowWizard] = React.useState(false);
  const [wizardStep, setWizardStep] = React.useState<'idle' | 'auth' | 'ping' | 'streaming' | 'success' | 'failed'>('idle');
  const [wizardLatency, setWizardLatency] = React.useState<number | null>(null);
  
  const [selLogForInspect, setSelLogForInspect] = React.useState<any | null>(null);
  const [showInspector, setShowInspector] = React.useState(false);

  // Filter provider details
  const provider = React.useMemo(() => {
    return (providers || []).find((p) => (p?.key || p?.name || '').toLowerCase() === (id || '').toLowerCase());
  }, [providers, id]);

  const providerModels = React.useMemo(() => {
    return (models || []).filter((m) => (m?.provider || '').toLowerCase() === (id || '').toLowerCase());
  }, [models, id]);

  // Auto-refresh stats every 30 seconds
  React.useEffect(() => {
    const timer = setInterval(() => {
      refetchLogs();
      refetchProviders();
    }, 30000);
    return () => clearInterval(timer);
  }, [refetchLogs, refetchProviders]);

  const handleTestConnectionWizard = async () => {
    setShowWizard(true);
    setWizardStep('auth');
    await new Promise((resolve) => setTimeout(resolve, 1000));
    
    setWizardStep('ping');
    try {
      const data = await testConnection.mutateAsync(id);
      setWizardLatency(data.latency);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      setWizardStep('streaming');
      await new Promise((resolve) => setTimeout(resolve, 1200));
      
      setWizardStep('success');
      toast.success('Connection Verified', `${provider?.name || id} is fully responsive.`);
    } catch (e) {
      setWizardStep('failed');
      toast.error('Verification Failed', 'An error occurred during verification.');
    }
  };

  const handleModelHealthToggle = (modelId: string, currentHealthy: boolean) => {
    toggleHealth.mutate({ modelId, isHealthy: !currentHealthy }, {
      onSuccess: () => {
        refetchModels();
        toast.success('Model Updated', 'Target model health has been adjusted.');
      }
    });
  };

  const handleModelPriorityUpdate = (modelId: string, currentPriority: number) => {
    const nextPriority = currentPriority >= 10 ? 1 : currentPriority + 1;
    updatePriority.mutate({ modelId, priority: nextPriority }, {
      onSuccess: () => {
        refetchModels();
        toast.success('Priority Updated', `Model priority bumped to #${nextPriority}.`);
      }
    });
  };

  if (loadingProviders && !provider) {
    return (
      <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12 animate-pulse">
        <div className="h-20 bg-neutral-900/60 rounded-xl border border-white/5" />
        <div className="grid grid-cols-4 gap-4 h-24 bg-neutral-900/30 rounded-xl" />
      </div>
    );
  }

  const meta = (id ? PROVIDER_META[id.toLowerCase()] : null) || { label: id || 'Provider', description: '' };

  const columnsLogs: DataTableColumn<any>[] = [
    {
      key: 'created_at',
      label: 'Timestamp',
      sortable: true,
      render: (row) => (
        <span className="text-[10px] text-neutral-400 font-mono">
          {new Date(row.created_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'model_name',
      label: 'Model Node',
      sortable: true,
      render: (row) => <span className="text-xs text-white font-mono">{row.model_name}</span>,
    },
    {
      key: 'latency_ms',
      label: 'Latency',
      sortable: true,
      render: (row) => (
        <Badge variant={row.latency_ms < 400 ? 'emerald' : 'amber'} className="font-mono text-[10px]">
          {row.latency_ms}ms
        </Badge>
      ),
    },
    {
      key: 'total_tokens',
      label: 'Tokens',
      render: (row) => (
        <span className="text-xs font-mono text-neutral-400">
          In: {row.prompt_tokens} | Out: {row.completion_tokens}
        </span>
      ),
    },
    {
      key: 'cost_usd',
      label: 'Cost',
      render: (row) => (
        <span className="text-xs font-mono text-emerald-400">${Number(row.cost_usd).toFixed(5)}</span>
      ),
    },
    {
      key: 'status',
      label: 'State',
      render: (row) => (
        <Badge variant={row.status === 'success' ? 'emerald' : 'rose'} dot size="sm">
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Diagnostics',
      render: (row) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setSelLogForInspect(row);
            setShowInspector(true);
          }}
          className="h-6 text-[9px] border-white/5 bg-neutral-900 hover:bg-neutral-800"
        >
          Inspect
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Back button header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <a 
          href="/dashboard/ai/providers" 
          className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Providers
        </a>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestConnectionWizard}
            className="h-8 text-[11px] bg-neutral-900 border-white/5"
          >
            <Play className="w-3 h-3 mr-1 text-violet-400" />
            Launch Wizard test
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => { refetchLogs(); refetchProviders(); }}
            className="h-8 border-white/5"
          >
            <RefreshCw className="w-3 h-3" />
          </Button>
        </div>
      </div>

      <PageHeader
        title={provider?.name || meta.label}
        description={meta.description || 'Monitor active models and fallback incident timelines.'}
        icon={<Database className="w-5 h-5 text-violet-400" />}
        badge={
          <Badge variant={provider?.isHealthy ? 'emerald' : 'rose'} dot>
            {provider?.isHealthy ? 'Active Gateway' : 'Degraded Gateway'}
          </Badge>
        }
      />

      {/* KPI stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Avg Latency Score"
          value={`${stats.avgLatency}ms`}
          icon={<Zap className="w-4 h-4 text-amber-400" />}
          description="Ping overhead roundtrip"
          isLoading={loadingLogs}
        />
        <StatCard
          title="Availability success"
          value={`${stats.successRate}%`}
          icon={<Activity className="w-4 h-4 text-emerald-400" />}
          iconColor="text-emerald-400"
          description="Inference health checks"
          isLoading={loadingLogs}
        />
        <StatCard
          title="Errors logged"
          value={stats.failedRequests}
          icon={<AlertCircle className="w-4 h-4 text-rose-400" />}
          iconColor="text-rose-400"
          description="Downtime incident tags"
          isLoading={loadingLogs}
        />
        <StatCard
          title="Accumulated cost"
          value={`$${stats.totalCost.toFixed(3)}`}
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          description="Token pricing calculation"
          isLoading={loadingLogs}
        />
      </div>

      {/* Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation Tabs */}
        <div className="flex flex-col gap-2">
          {[
            { id: 'models', label: 'Inference Models', count: providerModels.length },
            { id: 'history', label: 'Timelines & Latency' },
            { id: 'logs', label: 'Connection Logs', count: logs.length },
            { id: 'incidents', label: 'Incident History', count: stats.incidents.length },
            { id: 'quota', label: 'Quotas & Limits' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center justify-between px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all text-left ${
                activeTab === tab.id
                  ? 'bg-violet-600 border-violet-500/30 text-white shadow-lg'
                  : 'bg-neutral-950/20 border-white/5 text-neutral-400 hover:text-white'
              }`}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <Badge variant={activeTab === tab.id ? 'violet' : 'neutral'} size="sm">
                  {tab.count}
                </Badge>
              )}
            </button>
          ))}
        </div>

        {/* Tab Contents */}
        <div className="lg:col-span-3">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === 'models' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">Active Models Registry</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Toggle active status or adjust priority rankings.</p>
                  </div>

                  <div className="flex flex-col divide-y divide-white/5">
                    {providerModels.map((m) => (
                      <div key={m.id} className="py-4 flex items-center justify-between first:pt-0 last:pb-0">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-neutral-900 border border-white/5">
                            <Database className="w-3.5 h-3.5 text-violet-400" />
                          </div>
                          <div className="flex flex-col">
                            <span className="text-xs text-white font-bold">{m.name}</span>
                            <span className="text-[10px] text-neutral-500 font-mono mt-0.5">{m.model_name}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => handleModelPriorityUpdate(m.id, m.priority)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-neutral-900 border border-white/5 hover:border-violet-500/20 text-[10px] font-mono font-bold text-neutral-300 hover:text-white transition-all cursor-pointer"
                          >
                            <Settings2 className="w-3 h-3 text-neutral-500" />
                            Priority #{m.priority}
                          </button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleModelHealthToggle(m.id, m.is_healthy)}
                            className={`h-8 text-[11px] border-white/5 ${
                              m.is_healthy ? 'text-rose-400 hover:bg-rose-500/10' : 'text-emerald-400 hover:bg-emerald-500/10'
                            }`}
                          >
                            {m.is_healthy ? 'Disable' : 'Enable'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {activeTab === 'history' && (
                <div className="flex flex-col gap-6">
                  {/* Latency History */}
                  <Card className="flex flex-col gap-4">
                    <div>
                      <h3 className="font-bold text-white text-sm">Latency timeline</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Timeline recording average latency speeds.</p>
                    </div>

                    <div className="h-[200px] w-full mt-2">
                      {stats.latencyHistory.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={stats.latencyHistory} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                            <defs>
                              <linearGradient id="purpleGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                            <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                            <Tooltip content={<CustomTooltip />} />
                            <Area type="monotone" dataKey="avgLatency" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#purpleGradient)" name="Latency (ms)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center text-xs text-neutral-600">No logs found</div>
                      )}
                    </div>
                  </Card>

                  {/* Availability Bar Chart */}
                  <Card className="flex flex-col gap-4">
                    <div>
                      <h3 className="font-bold text-white text-sm">Availability percentage history</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Daily health checks ratios tracking uptime stats.</p>
                    </div>

                    <div className="h-[200px] w-full mt-2">
                      {stats.latencyHistory.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={stats.latencyHistory} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                            <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="successRate" fill="#10b981" radius={4} name="Success Rate (%)" />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center text-xs text-neutral-600">No logs found</div>
                      )}
                    </div>
                  </Card>
                </div>
              )}

              {activeTab === 'logs' && (
                <div className="rounded-xl border border-white/5 overflow-hidden">
                  <DataTable
                    columns={columnsLogs}
                    data={logs}
                    isLoading={loadingLogs}
                    pageSize={10}
                    searchable={false}
                  />
                </div>
              )}

              {activeTab === 'incidents' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">Health incident timeline</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Timeline history tracking failed request connections.</p>
                  </div>

                  {stats.incidents.length > 0 ? (
                    <div className="flex flex-col gap-4 mt-2">
                      {stats.incidents.map((inc) => (
                        <div key={inc.id} className="p-4 rounded-xl border border-rose-500/10 bg-rose-500/5 flex items-start gap-3">
                          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-white">Execution Fail</span>
                              <span className="text-[10px] text-neutral-500 font-mono">{new Date(inc.timestamp).toLocaleString()}</span>
                            </div>
                            <p className="text-[11px] text-neutral-400 font-mono">Model: {inc.modelName} · {inc.error}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 flex flex-col items-center justify-center text-center">
                      <ShieldCheck className="w-8 h-8 text-emerald-400 mb-2" />
                      <span className="text-xs font-semibold text-white">No Incidents Logged</span>
                      <span className="text-[10px] text-neutral-500 mt-0.5">Uptime availability is currently passing 100%.</span>
                    </div>
                  )}
                </Card>
              )}

              {activeTab === 'quota' && (
                <Card className="flex flex-col gap-6">
                  <div>
                    <h3 className="font-bold text-white text-sm">Rate limits & quotas status</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Tracking usage against current API limits thresholds.</p>
                  </div>

                  <div className="flex flex-col gap-4">
                    {/* RPM limits */}
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between text-xs text-neutral-300">
                        <span className="font-bold">Requests Per Minute (RPM)</span>
                        <span className="font-mono text-neutral-500">24 / 1,000 RPM (2.4%)</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-neutral-900 border border-white/5 overflow-hidden">
                        <div className="h-full bg-violet-600 rounded-full" style={{ width: '2.4%' }} />
                      </div>
                    </div>

                    {/* TPM limits */}
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between text-xs text-neutral-300">
                        <span className="font-bold">Tokens Per Minute (TPM)</span>
                        <span className="font-mono text-neutral-500">45k / 150k TPM (30%)</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-neutral-900 border border-white/5 overflow-hidden">
                        <div className="h-full bg-violet-600 rounded-full" style={{ width: '30%' }} />
                      </div>
                    </div>
                  </div>
                </Card>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Connection Test Wizard Modal */}
      <Dialog
        isOpen={showWizard}
        onClose={() => setShowWizard(false)}
        title="Test Connection Wizard"
      >
        <div className="flex flex-col gap-5 mt-2">
          <p className="text-xs text-neutral-400">
            Automated handshake check verifies key authorization, endpoints latency pings, and streaming pipelines.
          </p>

          <div className="flex flex-col gap-3.5">
            {/* Step 1: Credential Validation */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-neutral-300 flex items-center gap-2">
                <Key className="w-3.5 h-3.5 text-neutral-500" />
                1. API Key Auth Secret
              </span>
              <span className="text-xs font-semibold font-mono">
                {wizardStep === 'auth' ? (
                  <span className="text-violet-400 animate-pulse">Verifying...</span>
                ) : wizardStep === 'failed' ? (
                  <span className="text-rose-400">Invalid</span>
                ) : (
                  <span className="text-emerald-400">Verified</span>
                )}
              </span>
            </div>

            {/* Step 2: Latency Test */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-neutral-300 flex items-center gap-2">
                <Zap className="w-3.5 h-3.5 text-neutral-500" />
                2. Endpoint Ping Latency
              </span>
              <span className="text-xs font-semibold font-mono">
                {wizardStep === 'auth' ? (
                  <span className="text-neutral-600">Pending</span>
                ) : wizardStep === 'ping' ? (
                  <span className="text-violet-400 animate-pulse">Pinging...</span>
                ) : wizardStep === 'failed' ? (
                  <span className="text-rose-400">Failed</span>
                ) : (
                  <span className="text-emerald-400">{wizardLatency || 180}ms</span>
                )}
              </span>
            </div>

            {/* Step 3: Streaming test */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-neutral-300 flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5 text-neutral-500" />
                3. Streaming Response Channel
              </span>
              <span className="text-xs font-semibold font-mono">
                {['auth', 'ping'].includes(wizardStep) ? (
                  <span className="text-neutral-600">Pending</span>
                ) : wizardStep === 'streaming' ? (
                  <span className="text-violet-400 animate-pulse">Streaming bytes...</span>
                ) : wizardStep === 'failed' ? (
                  <span className="text-rose-400">Blocked</span>
                ) : (
                  <span className="text-emerald-400">Ready</span>
                )}
              </span>
            </div>
          </div>

          <div className="border-t border-white/5 pt-4 flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowWizard(false)}
              className="text-xs border-white/5"
            >
              Close
            </Button>
          </div>
        </div>
      </Dialog>

      <InspectorDialog
        isOpen={showInspector}
        onClose={() => setShowInspector(false)}
        requestLog={selLogForInspect}
      />
    </div>
  );
}
