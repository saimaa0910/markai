'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  Router, Layers, Activity, Sliders, Play, Trash2, Cpu, CheckCircle2, 
  AlertCircle, Sparkles, Plus, ToggleLeft, ToggleRight, Info
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function RouterDashboardPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = React.useState<'overview' | 'rules' | 'simulator'>('overview');
  
  // Simulator form state
  const [simPrompt, setSimPrompt] = React.useState('Write a Python function to compute Fibonacci sequence.');
  const [simType, setSimType] = React.useState('chat');
  const [simStrategy, setSimStrategy] = React.useState('balanced');
  const [simBalancer, setSimBalancer] = React.useState('priority');
  const [simEnv, setSimEnv] = React.useState('development');

  // Policy form state (for rule creation modal)
  const [showAddModal, setShowAddModal] = React.useState(false);
  const [newRuleName, setNewRuleName] = React.useState('');
  const [newRuleStrategy, setNewRuleStrategy] = React.useState('balanced');
  const [newRuleType, setNewRuleType] = React.useState('chat');
  const [newRulePriority, setNewRulePriority] = React.useState(10);
  const [newRuleTask, setNewRuleTask] = React.useState('');
  const [newRuleEnv, setNewRuleEnv] = React.useState('production');

  // Queries
  const strategiesQuery = useQuery({
    queryKey: ['router-strategies'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/router/strategies');
      return res.data || [];
    }
  });

  const rulesQuery = useQuery({
    queryKey: ['router-rules'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/router/rules');
      return res.data || [];
    }
  });

  const analyticsQuery = useQuery({
    queryKey: ['router-analytics'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/router/analytics');
      return res.data;
    },
    refetchInterval: 10000
  });

  const failoversQuery = useQuery({
    queryKey: ['router-failovers'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/router/failovers');
      return res.data || [];
    }
  });

  const healthQuery = useQuery({
    queryKey: ['router-health'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/router/health');
      return res.data || [];
    }
  });

  // Mutations
  const simulateMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/ai/router/simulate', {
        prompt: simPrompt,
        request_type: simType,
        strategy: simStrategy,
        environment: simEnv,
        load_balancer: simBalancer
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success('Simulation Complete', 'Intelligent routing choice retrieved successfully.');
    }
  });

  const createRuleMutation = useMutation({
    mutationFn: async (rule: any) => {
      const res = await apiClient.post('/ai/router/rules', rule);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['router-rules'] });
      setShowAddModal(false);
      setNewRuleName('');
      setNewRuleTask('');
      toast.success('Rule Created', 'Successfully added the new routing policy rule.');
    }
  });

  const toggleRuleMutation = useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      const res = await apiClient.put(`/ai/router/rules/${id}`, { is_active });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['router-rules'] });
      toast.success('Rule Status Updated', 'Rule status updated successfully.');
    }
  });

  const deleteRuleMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/ai/router/rules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['router-rules'] });
      toast.success('Rule Deleted', 'Routing policy rule removed successfully.');
    }
  });

  const handleAddRuleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleName) return;
    const conditions: Record<string, string> = {};
    if (newRuleTask) conditions['task'] = newRuleTask;
    conditions['environment'] = newRuleEnv;

    createRuleMutation.mutate({
      name: newRuleName,
      scope: 'organization',
      request_type: newRuleType,
      routing_strategy: newRuleStrategy,
      priority: Number(newRulePriority),
      conditions,
      is_active: true
    });
  };

  const analytics = analyticsQuery.data || { kpis: { total_requests: 0, success_rate: 100, total_cost_usd: 0, avg_latency_ms: 0, fallback_count: 0, retry_count: 0 }, live_feed: [] };
  const rules = rulesQuery.data || [];
  const failovers = failoversQuery.data || [];
  const healthList = healthQuery.data || [];
  const strategies = strategiesQuery.data || [];
  const simulation = simulateMutation.data;

  // Chart aggregation
  const providerStats = React.useMemo(() => {
    const stats: Record<string, number> = {};
    analytics.live_feed.forEach((f: any) => {
      stats[f.provider] = (stats[f.provider] || 0) + 1;
    });
    return Object.entries(stats).map(([name, count]) => ({ name, count }));
  }, [analytics.live_feed]);

  return (
    <div className="flex flex-col gap-6 max-w-[1450px] mx-auto pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-white/5 pb-4 gap-4">
        <PageHeader
          title="Enterprise AI Router"
          description="Centralized routing engine orchestrating policy-based failover, cost caps, and smart model parameters."
          icon={<Router className="w-5 h-5 text-violet-400" />}
          badge={<Badge variant="violet">Phase 1B Core</Badge>}
        />
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              analyticsQuery.refetch();
              rulesQuery.refetch();
              failoversQuery.refetch();
              healthQuery.refetch();
            }}
            className="h-8 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
          >
            Sync Telemetry
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Decisions"
          value={analytics.kpis.total_requests}
          icon={<Router className="w-4 h-4 text-violet-400" />}
          description="Routes orchestrated"
          isLoading={analyticsQuery.isLoading}
        />
        <StatCard
          title="Routing Success"
          value={`${analytics.kpis.success_rate}%`}
          icon={<CheckCircle2 className="w-4 h-4 text-emerald-400" />}
          description={`${analytics.kpis.retry_count} retries executed`}
          isLoading={analyticsQuery.isLoading}
        />
        <StatCard
          title="Average Latency"
          value={`${analytics.kpis.avg_latency_ms.toFixed(0)}ms`}
          icon={<Activity className="w-4 h-4 text-sky-400" />}
          description="Average transaction speed"
          isLoading={analyticsQuery.isLoading}
        />
        <StatCard
          title="Total Cost"
          value={`$${analytics.kpis.total_cost_usd.toFixed(4)}`}
          icon={<Layers className="w-4 h-4 text-amber-400" />}
          description="Accumulated model spend"
          isLoading={analyticsQuery.isLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="flex flex-col gap-2">
          {[
            { id: 'overview', label: 'Router KPIs Overview', icon: <Activity className="w-4 h-4" /> },
            { id: 'rules', label: 'Routing Policies Engine', icon: <Sliders className="w-4 h-4" /> },
            { id: 'simulator', label: 'Router Simulator Lab', icon: <Play className="w-4 h-4" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-semibold text-left transition-all ${
                activeTab === tab.id
                  ? 'bg-violet-600 border-violet-500/30 text-white shadow-lg'
                  : 'bg-neutral-950/20 border-white/5 text-neutral-400 hover:text-white'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="lg:col-span-3">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === 'overview' && (
                <div className="flex flex-col gap-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="md:col-span-2 flex flex-col gap-4">
                      <span className="text-xs font-bold text-white">Provider Usage Distribution</span>
                      <div className="h-48 w-full">
                        {providerStats.length === 0 ? (
                          <div className="h-full flex items-center justify-center text-[11px] text-neutral-500">No requests log data available.</div>
                        ) : (
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={providerStats}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" />
                              <XAxis dataKey="name" stroke="#666" fontSize={10} />
                              <YAxis stroke="#666" fontSize={10} />
                              <Tooltip />
                              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                                {providerStats.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#8b5cf6' : '#ec4899'} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        )}
                      </div>
                    </Card>

                    <Card className="flex flex-col gap-4">
                      <span className="text-xs font-bold text-white">Model Registry Health</span>
                      <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
                        {healthList.map((m: any) => (
                          <div key={m.model_name} className="flex justify-between items-center text-[10px] font-mono border-b border-white/5 pb-1">
                            <span className="text-neutral-300 font-bold truncate max-w-[120px]">{m.model_name}</span>
                            <div className="flex items-center gap-1.5">
                              <span>{m.avg_latency_sec}s</span>
                              <span className={`w-1.5 h-1.5 rounded-full ${m.is_healthy ? 'bg-emerald-400' : 'bg-rose-500'}`} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </Card>
                  </div>

                  <Card className="flex flex-col gap-4">
                    <span className="text-xs font-bold text-white">Live Requests Routing Feed</span>
                    <div className="flex flex-col gap-2 max-h-72 overflow-y-auto pr-1">
                      {analytics.live_feed.length === 0 ? (
                        <div className="text-[11px] text-neutral-500 py-4">No recent decisions captured.</div>
                      ) : (
                        analytics.live_feed.map((f: any) => (
                          <div key={f.id} className="p-3 border border-white/5 bg-neutral-950/40 rounded-xl flex items-center justify-between text-xs font-mono">
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-white">{f.model}</span>
                                <Badge variant="outline">{f.request_type}</Badge>
                                <Badge variant={f.success ? 'emerald' : 'rose'}>{f.success ? 'SUCCESS' : 'FAILED'}</Badge>
                              </div>
                              <span className="text-[10px] text-neutral-500">Strategy: {f.strategy}</span>
                            </div>
                            <div className="flex flex-col items-end gap-1 text-[10px] text-neutral-500">
                              <span>{f.latency_ms}ms — ${f.cost_usd.toFixed(5)}</span>
                              <span>{new Date(f.created_at).toLocaleTimeString()}</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                </div>
              )}

              {activeTab === 'rules' && (
                <Card className="flex flex-col gap-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-white text-sm">Active Routing Policies</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Evaluate conditional rule overrides matching tasks or projects scopes.</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddModal(true)}
                      className="h-8 border-violet-500/20 text-violet-400 bg-violet-950/10 hover:bg-violet-950/20"
                    >
                      <Plus className="w-3.5 h-3.5 mr-1" />
                      Create Rule
                    </Button>
                  </div>

                  <div className="flex flex-col gap-3">
                    {rules.length === 0 ? (
                      <div className="p-8 border border-dashed border-white/5 rounded-xl text-center text-xs text-neutral-500">
                        No custom routing override rules found. Seeding defaults for initial installation.
                      </div>
                    ) : (
                      rules.map((rule: any) => (
                        <div key={rule.id} className="p-4 border border-white/5 bg-neutral-950/40 rounded-xl flex items-center justify-between">
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-white">{rule.name}</span>
                              <Badge variant="violet">Priority {rule.priority}</Badge>
                              {rule.conditions && Object.keys(rule.conditions).length > 0 && (
                                <Badge variant="outline">
                                  {Object.entries(rule.conditions).map(([k, v]) => `${k}=${v}`).join(', ')}
                                </Badge>
                              )}
                            </div>
                            <span className="text-[10px] text-neutral-500 font-mono">
                              Strategy: {rule.routing_strategy} | Target Type: {rule.request_type}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => toggleRuleMutation.mutate({ id: rule.id, is_active: !rule.is_active })}
                              className="text-neutral-400 hover:text-white"
                            >
                              {rule.is_active ? <ToggleRight className="w-5 h-5 text-emerald-400" /> : <ToggleLeft className="w-5 h-5 text-neutral-500" />}
                            </button>
                            <button
                              onClick={() => deleteRuleMutation.mutate(rule.id)}
                              className="text-neutral-500 hover:text-rose-400 p-1 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </Card>
              )}

              {activeTab === 'simulator' && (
                <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                  <Card className="md:col-span-2 flex flex-col gap-4">
                    <span className="text-xs font-bold text-white">Simulator Inputs</span>
                    
                    <div className="flex flex-col gap-3 text-xs">
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] text-neutral-500 font-bold">PROMPT INPUT</label>
                        <textarea
                          value={simPrompt}
                          onChange={(e) => setSimPrompt(e.target.value)}
                          className="p-2.5 rounded-lg border border-white/5 bg-neutral-900 text-white min-h-[80px]"
                        />
                      </div>

                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] text-neutral-500 font-bold">REQUEST TYPE</label>
                        <select
                          value={simType}
                          onChange={(e) => setSimType(e.target.value)}
                          className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                        >
                          <option value="chat">Chat Completion</option>
                          <option value="embeddings">Embeddings</option>
                          <option value="vision">Vision</option>
                          <option value="json">JSON Mode</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] text-neutral-500 font-bold">ROUTING STRATEGY</label>
                        <select
                          value={simStrategy}
                          onChange={(e) => setSimStrategy(e.target.value)}
                          className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                        >
                          {strategies.map((s: any) => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                          ))}
                        </select>
                      </div>

                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] text-neutral-500 font-bold">LOAD BALANCER</label>
                        <select
                          value={simBalancer}
                          onChange={(e) => setSimBalancer(e.target.value)}
                          className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                        >
                          <option value="priority">Priority Routing</option>
                          <option value="round_robin">Round Robin</option>
                          <option value="least_loaded">Least Loaded</option>
                          <option value="random">Random Shuffling</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] text-neutral-500 font-bold">ENVIRONMENT</label>
                        <select
                          value={simEnv}
                          onChange={(e) => setSimEnv(e.target.value)}
                          className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                        >
                          <option value="development">Development</option>
                          <option value="production">Production</option>
                        </select>
                      </div>

                      <Button
                        onClick={() => simulateMutation.mutate()}
                        disabled={simulateMutation.isPending}
                        className="w-full mt-2 bg-violet-600 hover:bg-violet-500 text-white"
                      >
                        Run Route Simulation
                      </Button>
                    </div>
                  </Card>

                  <Card className="md:col-span-3 flex flex-col gap-4">
                    <span className="text-xs font-bold text-white">Simulation Decision Output</span>
                    
                    {simulation ? (
                      <div className="flex flex-col gap-4 text-xs font-mono">
                        <div className="p-4 border border-violet-500/20 bg-violet-950/10 rounded-xl flex items-center gap-3">
                          <Sparkles className="w-5 h-5 text-violet-400 shrink-0" />
                          <div className="flex flex-col">
                            <span className="font-bold text-white text-sm">{simulation.selected_model}</span>
                            <span className="text-[10px] text-neutral-500">Provider: {simulation.selected_provider.toUpperCase()}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3 text-[11px]">
                          <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-lg">
                            <span className="text-neutral-500">ESTIMATED LATENCY</span>
                            <p className="text-sm font-bold text-white mt-0.5">{simulation.estimated_latency_sec}s</p>
                          </div>
                          <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-lg">
                            <span className="text-neutral-500">ESTIMATED SPEND</span>
                            <p className="text-sm font-bold text-white mt-0.5">${simulation.estimated_cost_usd.toFixed(6)}</p>
                          </div>
                        </div>

                        {simulation.fallbacks.length > 0 && (
                          <div className="flex flex-col gap-1.5">
                            <span className="text-[10px] text-neutral-500 font-bold">FALLBACK MODELS CHAIN</span>
                            <div className="flex flex-wrap gap-1.5">
                              {simulation.fallbacks.map((f: string, i: number) => (
                                <Badge key={f} variant="outline">{f}</Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="p-3 border border-white/5 bg-neutral-950/40 rounded-xl flex items-start gap-2 font-sans text-neutral-400">
                          <Info className="w-4 h-4 text-neutral-500 shrink-0 mt-0.5" />
                          <p className="text-[11px] leading-relaxed">{simulation.reason}</p>
                        </div>
                      </div>
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-neutral-500 p-8 border border-dashed border-white/5 rounded-xl">
                        Select configurations and run simulation to preview routing criteria engine output.
                      </div>
                    )}
                  </Card>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Add Policy Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md bg-neutral-950 border border-white/10 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
          >
            <h3 className="font-bold text-white text-base">Create Routing Policy Override</h3>
            
            <form onSubmit={handleAddRuleSubmit} className="flex flex-col gap-3 text-xs">
              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">RULE NAME</label>
                <input
                  type="text"
                  required
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  placeholder="e.g. Force Groq Llama for Chat development"
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">REQUEST TYPE</label>
                <select
                  value={newRuleType}
                  onChange={(e) => setNewRuleType(e.target.value)}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                >
                  <option value="*">Any (*)</option>
                  <option value="chat">Chat</option>
                  <option value="embeddings">Embeddings</option>
                  <option value="vision">Vision</option>
                  <option value="json">JSON Mode</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">ROUTING STRATEGY</label>
                <select
                  value={newRuleStrategy}
                  onChange={(e) => setNewRuleStrategy(e.target.value)}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                >
                  <option value="cheapest">Cheapest</option>
                  <option value="fastest">Fastest</option>
                  <option value="highest_quality">Highest Quality</option>
                  <option value="balanced">Balanced</option>
                  <option value="coding">Coding Focus</option>
                  <option value="vision">Vision Focus</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">PRIORITY RANK (Higher evaluates first)</label>
                <input
                  type="number"
                  value={newRulePriority}
                  onChange={(e) => setNewRulePriority(Number(e.target.value))}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">CONDITION MATCH: TASK (Optional)</label>
                <input
                  type="text"
                  value={newRuleTask}
                  onChange={(e) => setNewRuleTask(e.target.value)}
                  placeholder="e.g. coding"
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">CONDITION MATCH: ENVIRONMENT</label>
                <select
                  value={newRuleEnv}
                  onChange={(e) => setNewRuleEnv(e.target.value)}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                >
                  <option value="development">Development</option>
                  <option value="production">Production</option>
                </select>
              </div>

              <div className="flex gap-2 justify-end mt-4">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  className="bg-violet-600 hover:bg-violet-500 text-white"
                >
                  Save Policy
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
