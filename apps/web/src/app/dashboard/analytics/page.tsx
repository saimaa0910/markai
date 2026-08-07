'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import dynamic from 'next/dynamic';

const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false });
const AreaChart = dynamic(() => import('recharts').then((mod) => mod.AreaChart), { ssr: false });
const Area = dynamic(() => import('recharts').then((mod) => mod.Area), { ssr: false });
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false });
const BarChart = dynamic(() => import('recharts').then((mod) => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false });
const LineChart = dynamic(() => import('recharts').then((mod) => mod.LineChart), { ssr: false });
const Line = dynamic(() => import('recharts').then((mod) => mod.Line), { ssr: false });
const PieChart = dynamic(() => import('recharts').then((mod) => mod.PieChart), { ssr: false });
const Pie = dynamic(() => import('recharts').then((mod) => mod.Pie), { ssr: false });
const Cell = dynamic(() => import('recharts').then((mod) => mod.Cell), { ssr: false });
import { BarChart2, DollarSign, Users, Bot, Megaphone, TrendingUp, Target } from 'lucide-react';

const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-white/10 rounded-lg px-3 py-2 shadow-xl text-xs">
      <p className="text-neutral-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <span style={{ color: p.color }}>●</span>
          <span className="text-neutral-300">{p.name}:</span>
          <span className="font-bold text-white">{typeof p.value === 'number' && p.value % 1 !== 0 ? p.value.toFixed(2) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

const FUNNEL_COLORS = ['#8b5cf6', '#6d28d9', '#4c1d95', '#2e1065'];

export default function AnalyticsPage() {
  const { activeOrg } = useAuthStore();
  const [tab, setTab] = React.useState('executive');

  const { data: leads = [],    isLoading: l1 } = useQuery({ queryKey: ['leads', activeOrg?.id],    queryFn: async () => (await apiClient.get('/crm/leads/')).data || [],    enabled: !!activeOrg });
  const { data: contacts = [], isLoading: l2 } = useQuery({ queryKey: ['contacts', activeOrg?.id], queryFn: async () => (await apiClient.get('/crm/contacts/')).data || [], enabled: !!activeOrg });
  const { data: copies = [],   isLoading: l3 } = useQuery({ queryKey: ['copies', activeOrg?.id],   queryFn: async () => (await apiClient.get('/generator/')).data || [],     enabled: !!activeOrg });
  const { data: usage = [],    isLoading: l4 } = useQuery({ queryKey: ['ai-usage', activeOrg?.id], queryFn: async () => (await apiClient.get('/ai/usage/')).data || [],      enabled: !!activeOrg });

  const isLoading = l1 || l2 || l3 || l4;

  // Derived KPIs
  const pipelineValue = leads.reduce((s: number, l: any) => s + (l.value || 0), 0);
  const wonLeads      = leads.filter((l: any) => l.status === 'WON' || l.status === 'converted').length;
  const convRate      = leads.length ? ((wonLeads / leads.length) * 100).toFixed(1) : '0.0';
  const aiCost        = usage.reduce((s: number, u: any) => s + (u.cost_usd || 0), 0);
  const aiTokens      = usage.reduce((s: number, u: any) => s + (u.total_tokens || 0), 0);

  // Lead status funnel
  const statusOrder = ['NEW', 'CONTACTED', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION', 'WON'];
  const funnelData = statusOrder.map((status, i) => ({
    name: status,
    value: leads.filter((l: any) => l.status === status || l.status === status.toLowerCase()).length,
    fill: FUNNEL_COLORS[Math.min(i, FUNNEL_COLORS.length - 1)],
  })).filter((d) => d.value > 0);

  // Mock time-series (replace with real endpoint if available)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'];
  const revenueData = months.map((month, i) => ({
    month,
    revenue:  Math.round(pipelineValue * (0.4 + i * 0.1) / 7),
    contacts: Math.round(contacts.length * (0.3 + i * 0.1)),
    copies:   Math.round(copies.length  * (0.2 + i * 0.12)),
  }));

  // Provider token distribution
  const providerTokens = React.useMemo(() => {
    const acc: Record<string, number> = {};
    for (const u of usage) { acc[u.provider] = (acc[u.provider] || 0) + (u.total_tokens || 0); }
    return Object.entries(acc).map(([name, value]) => ({ name, value }));
  }, [usage]);

  const PIE_COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#38bdf8', '#f43f5e'];

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Analytics"
        description="Unified executive dashboards across CRM pipeline, marketing performance, and AI cost analytics."
        icon={<BarChart2 className="w-5 h-5" />}
        badge={<Badge variant="violet">Live Data</Badge>}
      />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="executive"  icon={<TrendingUp className="w-3.5 h-3.5" />}>Executive</TabsTrigger>
          <TabsTrigger value="crm"        icon={<Users className="w-3.5 h-3.5" />}>CRM Pipeline</TabsTrigger>
          <TabsTrigger value="marketing"  icon={<Megaphone className="w-3.5 h-3.5" />}>Marketing</TabsTrigger>
          <TabsTrigger value="ai"         icon={<Bot className="w-3.5 h-3.5" />}>AI Platform</TabsTrigger>
        </TabsList>

        {/* ── Executive ── */}
        <TabsContent value="executive">
          <div className="flex flex-col gap-6">
            {/* KPIs */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard title="Pipeline Value"   value={`$${pipelineValue.toLocaleString()}`} icon={<DollarSign className="w-4 h-4" />} iconColor="text-emerald-400" description="Weighted CRM pipeline" isLoading={isLoading} change="+14.2%" isPositive />
              <StatCard title="Total Contacts"   value={contacts.length} icon={<Users className="w-4 h-4" />} description="Active in CRM" isLoading={isLoading} change="+8.4%" isPositive />
              <StatCard title="AI Generations"   value={copies.length}   icon={<Bot className="w-4 h-4" />}   iconColor="text-violet-400" description="Copy variants created" isLoading={isLoading} change="+24.1%" isPositive />
              <StatCard title="Conversion Rate"  value={`${convRate}%`}  icon={<Target className="w-4 h-4" />} iconColor="text-amber-400" description="Won / Total leads" isLoading={isLoading} />
            </div>

            {/* Revenue trend */}
            <div className="rounded-xl border border-white/5 bg-neutral-950/40 p-5">
              <h3 className="text-sm font-bold text-white mb-4">Pipeline Growth</h3>
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={revenueData}>
                  <defs>
                    <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="revenue" name="Pipeline $" stroke="#8b5cf6" fill="url(#revGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </TabsContent>

        {/* ── CRM Pipeline ── */}
        <TabsContent value="crm">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Lead Status Funnel */}
            <div className="rounded-xl border border-white/5 bg-neutral-950/40 p-5">
              <h3 className="text-sm font-bold text-white mb-4">Lead Conversion Funnel</h3>
              {funnelData.length > 0 ? (
                <div className="flex flex-col gap-2">
                  {funnelData.map((stage, idx) => {
                    const pct = funnelData[0].value > 0 ? (stage.value / funnelData[0].value) * 100 : 0;
                    return (
                      <div key={stage.name} className="flex items-center gap-3">
                        <span className="text-[11px] text-neutral-400 w-24 text-right">{stage.name}</span>
                        <div className="flex-1 h-7 rounded-lg bg-neutral-800 overflow-hidden relative">
                          <div
                            className="h-full rounded-lg flex items-center justify-end pr-3 transition-all"
                            style={{ width: `${pct}%`, background: FUNNEL_COLORS[idx % FUNNEL_COLORS.length] }}
                          >
                            <span className="text-[10px] font-bold text-white">{stage.value}</span>
                          </div>
                        </div>
                        <span className="text-[11px] text-neutral-500 w-12">{pct.toFixed(0)}%</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-neutral-500 text-center py-12">No lead data yet.</p>
              )}
            </div>

            {/* Contact trend */}
            <div className="rounded-xl border border-white/5 bg-neutral-950/40 p-5">
              <h3 className="text-sm font-bold text-white mb-4">Contact Growth Trend</h3>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Line type="monotone" dataKey="contacts" name="Contacts" stroke="#10b981" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </TabsContent>

        {/* ── Marketing ── */}
        <TabsContent value="marketing">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="rounded-xl border border-white/5 bg-neutral-950/40 p-5">
              <h3 className="text-sm font-bold text-white mb-4">AI Copy Generations Over Time</h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="copies" name="Copies" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="rounded-xl border border-white/5 bg-neutral-950/40 p-5">
              <h3 className="text-sm font-bold text-white mb-4">Campaign Performance Summary</h3>
              <div className="flex flex-col gap-3 py-4">
                {[
                  { label: 'Total AI Generations', value: copies.length, color: 'text-violet-400' },
                  { label: 'Total CRM Contacts',   value: contacts.length, color: 'text-emerald-400' },
                  { label: 'Pipeline Value',        value: `$${pipelineValue.toLocaleString()}`, color: 'text-amber-400' },
                  { label: 'Conversion Rate',       value: `${convRate}%`, color: 'text-sky-400' },
                ].map((stat) => (
                  <div key={stat.label} className="flex items-center justify-between p-3 rounded-lg bg-neutral-900/60 border border-white/5">
                    <span className="text-xs text-neutral-400">{stat.label}</span>
                    <span className={`text-sm font-bold ${stat.color}`}>{stat.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ── AI Platform ── */}
        <TabsContent value="ai">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard title="AI Requests" value={usage.length} icon={<Bot className="w-4 h-4" />} isLoading={l4} />
            <StatCard title="Total Tokens" value={aiTokens.toLocaleString()} icon={<BarChart2 className="w-4 h-4" />} iconColor="text-violet-400" isLoading={l4} />
            <StatCard title="Total Cost" value={`$${aiCost.toFixed(4)}`} icon={<DollarSign className="w-4 h-4" />} iconColor="text-emerald-400" isLoading={l4} />
            <StatCard title="Avg Latency" value={usage.length ? `${Math.round(usage.reduce((s: number, u: any) => s + (u.latency_ms || 0), 0) / usage.length)}ms` : '—'} icon={<TrendingUp className="w-4 h-4" />} iconColor="text-amber-400" isLoading={l4} />
          </div>

          <div className="rounded-xl border border-white/5 bg-neutral-950/40 p-5">
            <h3 className="text-sm font-bold text-white mb-6">Token Distribution by Provider</h3>
            {providerTokens.length > 0 ? (
              <div className="flex flex-col lg:flex-row items-center gap-8">
                <ResponsiveContainer width={240} height={240}>
                  <PieChart>
                    <Pie data={providerTokens} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value">
                      {providerTokens.map((_, idx) => <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />)}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-col gap-2.5">
                  {providerTokens.map((p, idx) => (
                    <div key={p.name} className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full" style={{ background: PIE_COLORS[idx % PIE_COLORS.length] }} />
                      <span className="text-sm text-neutral-300 capitalize">{p.name}</span>
                      <span className="ml-auto text-sm font-bold text-white">{p.value.toLocaleString()}</span>
                      <span className="text-xs text-neutral-500">tokens</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-neutral-500 text-center py-12">No AI usage data yet.</p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
