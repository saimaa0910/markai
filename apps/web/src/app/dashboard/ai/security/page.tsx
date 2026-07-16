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
  ShieldAlert, ShieldCheck, Lock, Activity, Sliders, Play, Trash2, Cpu, 
  CheckCircle2, AlertTriangle, Plus, ToggleLeft, ToggleRight, Info, Eye
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function SecurityCenterPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = React.useState<'overview' | 'policies' | 'quotas' | 'analytics'>('overview');
  
  // Rule Creation modal states
  const [showAddModal, setShowAddModal] = React.useState(false);
  const [newRuleName, setNewRuleName] = React.useState('');
  const [newDailyRequests, setNewDailyRequests] = React.useState(500);
  const [newDailyBudget, setNewDailyBudget] = React.useState(10.0);
  const [newPiiMasking, setNewPiiMasking] = React.useState('redact');
  const [newViolenceAction, setNewViolenceAction] = React.useState('block');
  const [newSecretsAction, setNewSecretsAction] = React.useState('block');

  // Queries
  const policiesQuery = useQuery({
    queryKey: ['security-policies'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/security/policies');
      return res.data || [];
    }
  });

  const eventsQuery = useQuery({
    queryKey: ['security-events'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/security/events');
      return res.data || [];
    },
    refetchInterval: 8000
  });

  const auditsQuery = useQuery({
    queryKey: ['security-audits'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/security/audit');
      return res.data || [];
    }
  });

  const quotasQuery = useQuery({
    queryKey: ['security-quotas'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/security/quotas');
      return res.data || [];
    }
  });

  const moderationQuery = useQuery({
    queryKey: ['security-moderation-stats'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/security/moderation');
      return res.data || {};
    }
  });

  // Mutations
  const createPolicyMutation = useMutation({
    mutationFn: async (rule: any) => {
      const res = await apiClient.post('/ai/security/policies', rule);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-policies'] });
      setShowAddModal(false);
      setNewRuleName('');
      toast.success('Security Policy Created', 'New governance compliance policy rule saved.');
    }
  });

  const deletePolicyMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/ai/security/policies/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-policies'] });
      toast.success('Policy Removed', 'Governance policy deleted successfully.');
    }
  });

  const togglePolicyMutation = useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      await apiClient.put(`/ai/security/policies/${id}`, { is_active });
    },    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-policies'] });
      toast.success('Policy Status Toggled', 'Compliance rule updated.');
    }
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleName) return;

    createPolicyMutation.mutate({
      name: newRuleName,
      scope: 'organization',
      daily_request_limit: Number(newDailyRequests),
      daily_budget_usd: Number(newDailyBudget),
      pii_masking_policy: newPiiMasking,
      moderation_actions: {
        violence: newViolenceAction,
        hate: 'block',
        harassment: 'block',
        sexual: 'redact',
        self_harm: 'block',
        pii: 'redact',
        secrets: newSecretsAction
      },
      is_active: true
    });
  };

  const policies = policiesQuery.data || [];
  const events = eventsQuery.data || [];
  const audits = auditsQuery.data || [];
  const quotas = quotasQuery.data || [];
  const modStats = moderationQuery.data || {};

  // Score evaluation
  const securityScore = React.useMemo(() => {
    if (events.length === 0) return 100;
    const criticalCount = events.filter((e: any) => e.severity === 'critical').length;
    const highCount = events.filter((e: any) => e.severity === 'high').length;
    const deduct = (criticalCount * 15) + (highCount * 5);
    return Math.max(40, 100 - deduct);
  }, [events]);

  const piiViolations = events.filter((e: any) => e.event_type === 'pii_leak').length;
  const secretsViolations = events.filter((e: any) => e.event_type === 'secret_leak').length;
  const blockedRequests = events.filter((e: any) => e.action_taken === 'block').length;

  // Chart aggregation
  const riskTrends = React.useMemo(() => {
    // Generate trend mapping based on audits risk scores
    const days: Record<string, { name: string; risk: number; count: number }> = {};
    audits.forEach((a: any) => {
      const dateStr = new Date(a.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      if (!days[dateStr]) {
        days[dateStr] = { name: dateStr, risk: 0, count: 0 };
      }
      days[dateStr].risk += parseFloat(a.risk_score);
      days[dateStr].count += 1;
    });
    return Object.values(days).map(d => ({
      name: d.name,
      'Risk Score': d.count ? Math.round((d.risk / d.count) * 100) / 100 : 0
    })).reverse();
  }, [audits]);

  return (
    <div className="flex flex-col gap-6 max-w-[1450px] mx-auto pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-white/5 pb-4 gap-4">
        <PageHeader
          title="AI Security Center"
          description="Centralized compliance sandbox orchestrating PII filters, secret leakage logs, content moderations, and quota limits."
          icon={<Lock className="w-5 h-5 text-violet-400" />}
          badge={<Badge variant="violet">Phase 1C Governance</Badge>}
        />
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              policiesQuery.refetch();
              eventsQuery.refetch();
              auditsQuery.refetch();
              quotasQuery.refetch();
              moderationQuery.refetch();
            }}
            className="h-8 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
          >
            Sync Governance
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Security Health Index"
          value={`${securityScore}/100`}
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
          description={`${events.length} compliance warnings`}
          isLoading={eventsQuery.isLoading}
        />
        <StatCard
          title="Intercepted Blocks"
          value={blockedRequests}
          icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
          description="Unauthorized attempts blocked"
          isLoading={eventsQuery.isLoading}
        />
        <StatCard
          title="PII Redacted Leaks"
          value={piiViolations}
          icon={<Eye className="w-4 h-4 text-sky-400" />}
          description="Compliance leaks scrubbed"
          isLoading={eventsQuery.isLoading}
        />
        <StatCard
          title="Secrets Shielded"
          value={secretsViolations}
          icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
          description="API / Database Keys shielded"
          isLoading={eventsQuery.isLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="flex flex-col gap-2">
          {[
            { id: 'overview', label: 'Monitoring Events Log', icon: <Activity className="w-4 h-4" /> },
            { id: 'policies', label: 'Governance Rules', icon: <Sliders className="w-4 h-4" /> },
            { id: 'quotas', label: 'Quotas & Budgets', icon: <Cpu className="w-4 h-4" /> },
            { id: 'analytics', label: 'Compliance Analytics', icon: <Info className="w-4 h-4" /> },
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
                  <Card className="flex flex-col gap-4">
                    <span className="text-xs font-bold text-white">Live Interceptions Event Feed</span>
                    <div className="flex flex-col gap-2 max-h-96 overflow-y-auto pr-1">
                      {events.length === 0 ? (
                        <div className="text-[11px] text-neutral-500 py-4 font-mono">No security rule violations logged today.</div>
                      ) : (
                        events.map((e: any) => (
                          <div key={e.id} className="p-3 border border-white/5 bg-neutral-950/40 rounded-xl flex items-center justify-between text-xs font-mono">
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-white">{e.event_type.toUpperCase()}</span>
                                <Badge variant={e.severity === 'critical' ? 'rose' : e.severity === 'high' ? 'rose' : 'amber'}>
                                  {e.severity.toUpperCase()}
                                </Badge>
                                <Badge variant="outline">{e.trigger_source.toUpperCase()} CHECK</Badge>
                              </div>
                              <span className="text-[10px] text-neutral-500">{e.details}</span>
                            </div>
                            <div className="flex flex-col items-end gap-1 text-[10px]">
                              <Badge variant={e.action_taken === 'block' ? 'rose' : 'emerald'}>
                                {e.action_taken.toUpperCase()}
                              </Badge>
                              <span className="text-neutral-500">{new Date(e.created_at).toLocaleTimeString()}</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>

                  <Card className="flex flex-col gap-4">
                    <span className="text-xs font-bold text-white">Real-time Prompt Scan Audits</span>
                    <div className="flex flex-col gap-2 max-h-72 overflow-y-auto pr-1">
                      {audits.length === 0 ? (
                        <div className="text-[11px] text-neutral-500 py-4 font-mono">No scan records available.</div>
                      ) : (
                        audits.map((a: any) => (
                          <div key={a.id} className="p-3 border border-white/5 bg-neutral-950/40 rounded-xl flex items-center justify-between text-xs font-mono">
                            <div className="flex flex-col gap-0.5">
                              <span className="font-bold text-neutral-200">Length: {a.prompt_length} chars | Complexity Rank: {a.prompt_complexity}</span>
                              <div className="flex gap-2 mt-1">
                                {a.pii_detected && <Badge variant="amber">PII Scanned</Badge>}
                                {a.secrets_detected && <Badge variant="rose">Secrets Blocked</Badge>}
                                <Badge variant="outline">Risk: {a.risk_score}</Badge>
                              </div>
                            </div>
                            <span className="text-[10px] text-neutral-500">{new Date(a.created_at).toLocaleTimeString()}</span>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                </div>
              )}

              {activeTab === 'policies' && (
                <Card className="flex flex-col gap-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-white text-sm">Security Policy Parameters</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Orchestrate PII filters and rate counters across environment modules.</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddModal(true)}
                      className="h-8 border-violet-500/20 text-violet-400 bg-violet-950/10 hover:bg-violet-950/20"
                    >
                      <Plus className="w-3.5 h-3.5 mr-1" />
                      Add Policy
                    </Button>
                  </div>

                  <div className="flex flex-col gap-3">
                    {policies.map((p: any) => (
                      <div key={p.id} className="p-4 border border-white/5 bg-neutral-950/40 rounded-xl flex items-center justify-between">
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">{p.name}</span>
                            <Badge variant="violet">{p.scope.toUpperCase()}</Badge>
                            <Badge variant="outline">PII: {p.pii_masking_policy.toUpperCase()}</Badge>
                          </div>
                          <span className="text-[10px] text-neutral-500 font-mono">
                            Daily Req Limit: {p.daily_request_limit} | Daily Spend Cap: ${p.daily_budget_usd}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => togglePolicyMutation.mutate({ id: p.id, is_active: !p.is_active })}
                            className="text-neutral-400 hover:text-white"
                          >
                            {p.is_active ? <ToggleRight className="w-5 h-5 text-emerald-400" /> : <ToggleLeft className="w-5 h-5 text-neutral-500" />}
                          </button>
                          {p.scope !== 'global' && (
                            <button
                              onClick={() => deletePolicyMutation.mutate(p.id)}
                              className="text-neutral-500 hover:text-rose-400 p-1 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {activeTab === 'quotas' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {quotas.length === 0 ? (
                    <Card className="col-span-2 text-center text-xs text-neutral-500 py-8">
                      No active quota usage calculations compiled yet. Quotas are recorded on first AI Gateway execution.
                    </Card>
                  ) : (
                    quotas.map((q: any) => (
                      <Card key={q.id} className="flex flex-col gap-4 font-mono text-xs">
                        <div className="flex justify-between items-center border-b border-white/5 pb-2">
                          <span className="font-bold text-white">Org Quota Allocation Usage</span>
                          <span className="text-[10px] text-neutral-500">Reset: {new Date(q.last_reset_date).toLocaleDateString()}</span>
                        </div>
                        
                        <div className="flex flex-col gap-3">
                          <div className="flex justify-between">
                            <span className="text-neutral-400">DAILY TOKENS</span>
                            <span className="text-white font-bold">{q.daily_tokens} tokens</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-neutral-400">DAILY REQUESTS</span>
                            <span className="text-white font-bold">{q.daily_requests} requests</span>
                          </div>
                          <div className="flex justify-between border-t border-white/5 pt-2">
                            <span className="text-neutral-400">DAILY BUDGET CONSUMED</span>
                            <span className="text-emerald-400 font-bold">${parseFloat(q.daily_spend).toFixed(4)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-neutral-400">MONTHLY TOKENS</span>
                            <span className="text-white font-bold">{q.monthly_tokens} tokens</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-neutral-400">MONTHLY SPEND</span>
                            <span className="text-emerald-400 font-bold">${parseFloat(q.monthly_spend).toFixed(4)}</span>
                          </div>
                        </div>
                      </Card>
                    ))
                  )}
                </div>
              )}

              {activeTab === 'analytics' && (
                <div className="flex flex-col gap-6">
                  <Card className="flex flex-col gap-4">
                    <span className="text-xs font-bold text-white">Governance Risk Trends</span>
                    <div className="h-60 w-full">
                      {riskTrends.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-[11px] text-neutral-500">No telemetry trend data compiled.</div>
                      ) : (
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={riskTrends}>
                            <defs>
                              <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" />
                            <XAxis dataKey="name" stroke="#666" fontSize={10} />
                            <YAxis stroke="#666" fontSize={10} />
                            <Tooltip />
                            <Area type="monotone" dataKey="Risk Score" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorRisk)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      )}
                    </div>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="flex flex-col gap-3 text-xs">
                      <span className="font-bold text-white">Triggered Moderation Categories</span>
                      <div className="flex flex-col gap-2 mt-2">
                        {Object.entries(modStats).length === 0 ? (
                          <div className="text-[10px] text-neutral-500 font-mono">No categories matched.</div>
                        ) : (
                          Object.entries(modStats).map(([cat, count]) => (
                            <div key={cat} className="flex justify-between items-center text-[10px] font-mono border-b border-white/5 pb-1">
                              <span className="text-neutral-400 capitalize">{cat}</span>
                              <Badge variant="rose">{count as number} matches</Badge>
                            </div>
                          ))
                        )}
                      </div>
                    </Card>

                    <Card className="flex flex-col gap-2 text-xs text-neutral-400 leading-relaxed">
                      <span className="font-bold text-white mb-2">Compliance Governance Guidelines</span>
                      <p>
                        The Governance layer enforces standard ISO and SOC-2 specifications automatically:
                      </p>
                      <ul className="list-disc list-inside mt-2 flex flex-col gap-1.5 text-[11px]">
                        <li>All API Keys are automatically encrypted.</li>
                        <li>Unsanitized prompts containing password strings are blocked.</li>
                        <li>Outputs containing credit cards leaks are redacted at runtime.</li>
                      </ul>
                    </Card>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md bg-neutral-950 border border-white/10 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
          >
            <h3 className="font-bold text-white text-base">Create Governance Policy</h3>
            
            <form onSubmit={handleCreateSubmit} className="flex flex-col gap-3 text-xs">
              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">POLICY NAME</label>
                <input
                  type="text"
                  required
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  placeholder="e.g. Strict Development Scanner"
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">DAILY REQUEST LIMIT</label>
                <input
                  type="number"
                  value={newDailyRequests}
                  onChange={(e) => setNewDailyRequests(Number(e.target.value))}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">DAILY SPEND BUDGET ($ USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newDailyBudget}
                  onChange={(e) => setNewDailyBudget(Number(e.target.value))}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">PII MASKING POLICY</label>
                <select
                  value={newPiiMasking}
                  onChange={(e) => setNewPiiMasking(e.target.value)}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                >
                  <option value="redact">Redact (Erase match)</option>
                  <option value="mask">Mask (Replace with stars)</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">VIOLENCE CATEGORY ACTION</label>
                <select
                  value={newViolenceAction}
                  onChange={(e) => setNewViolenceAction(e.target.value)}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                >
                  <option value="block">Block Prompt</option>
                  <option value="warn">Warn Only</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-neutral-500">SECRET LEAKAGE ACTION</label>
                <select
                  value={newSecretsAction}
                  onChange={(e) => setNewSecretsAction(e.target.value)}
                  className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-white"
                >
                  <option value="block">Block Prompt</option>
                  <option value="redact">Redact Keys</option>
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
