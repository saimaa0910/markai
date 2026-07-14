import * as React from 'react';
import { useUsage, useAnalytics } from '../hooks';
import { TokenCounter } from '../components/token-counter';
import { FilterPanel } from '../components/filter-panel';
import { ExportButton } from '../components/export-button';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { DataTable, DataTableColumn } from '@/components/ui/data-table';
import { InspectorDialog } from '../components/inspector-dialog';
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip,
  BarChart, Bar, CartesianGrid, PieChart, Pie, Cell, Legend
} from 'recharts';
import { 
  BarChart3, DollarSign, Zap, Activity, HardDrive, CheckCircle2, 
  XCircle, Filter, HelpCircle, Users, Building2 
} from 'lucide-react';
import { useAIPlatformStore } from '../store/ai-platform';

const CHART_COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#38bdf8', '#f43f5e', '#ec4899'];

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

export function UsagePage() {
  const { usage, kpis, isLoading, refetch } = useUsage();
  const { charts, performanceBreakdown } = useAnalytics();
  const { searchQuery, selectedProvider, selectedModel } = useAIPlatformStore();

  const [selLogForInspect, setSelLogForInspect] = React.useState<any | null>(null);
  const [showInspector, setShowInspector] = React.useState(false);

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
        <span className="text-xs font-mono text-neutral-400 font-bold">
          {row.total_tokens} t
        </span>
      ),
    },
    {
      key: 'cost_usd',
      label: 'Cost',
      render: (row) => (
        <span className="text-xs font-mono text-emerald-400 font-bold">${Number(row.cost_usd).toFixed(5)}</span>
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

  // Filter raw usage for search/provider overrides
  const filteredUsage = React.useMemo(() => {
    return usage.filter((u) => {
      if (selectedProvider && u.provider !== selectedProvider) return false;
      if (selectedModel && u.model_name !== selectedModel) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return u.model_name.toLowerCase().includes(q) || 
               u.provider.toLowerCase().includes(q);
      }
      return true;
    });
  }, [usage, selectedProvider, selectedModel, searchQuery]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Usage Telemetry"
        description="Monitor system-wide query requests, cost aggregation audits, and token throughput limits in real-time."
        icon={<BarChart3 className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Metrics Live</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <ExportButton data={filteredUsage} filename={`eaimos_gateway_usages_${new Date().toLocaleDateString()}.csv`} />
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="h-8 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
            >
              Sync
            </Button>
          </div>
        }
      />

      {/* KPI Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total API Calls"
          value={kpis.totalRequests}
          icon={<Activity className="w-4 h-4 text-violet-400" />}
          description="Integrated provider queries"
          isLoading={isLoading}
        />
        <StatCard
          title="Avg Latency Speed"
          value={`${kpis.avgLatency}ms`}
          icon={<Zap className="w-4 h-4 text-amber-400" />}
          description="Gateway roundtrip overhead"
          isLoading={isLoading}
        />
        <StatCard
          title="Failing Requests"
          value={kpis.failedRequests}
          icon={<XCircle className="w-4 h-4 text-rose-400" />}
          iconColor="text-rose-400"
          description="Failed model processing logs"
          isLoading={isLoading}
        />
        <StatCard
          title="Accumulated Cost"
          value={`$${kpis.totalCost.toFixed(4)}`}
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          description="Tokens price calculation"
          isLoading={isLoading}
        />
      </div>

      {/* Token details badge row */}
      <TokenCounter
        promptTokens={kpis.promptTokens}
        completionTokens={kpis.completionTokens}
        totalTokens={kpis.totalTokens}
        label="Accumulated Gateway Token Volume"
      />

      {/* Filter panel */}
      <FilterPanel onRefresh={refetch} />

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost trends / Request timeline */}
        <Card className="lg:col-span-2 flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Token Request Volume & Cost Trends</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">Timeline trends for overall request volume mapped with cost accumulation.</p>
          </div>
          
          <div className="h-[250px] w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts.timeSeries} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="purpleArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="requests" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#purpleArea)" name="Queries" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Provider distribution */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Provider Query Allocation</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">Percentage breakdown of queries mapped to LLM gateways.</p>
          </div>

          <div className="h-[200px] w-full flex items-center justify-center relative">
            {charts.providerDist.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.providerDist}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {charts.providerDist.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-xs text-neutral-600">No logs logged</span>
            )}
          </div>
          
          <div className="flex flex-wrap gap-x-3 gap-y-1.5 justify-center text-[10px] text-neutral-400">
            {charts.providerDist.map((item, idx) => (
              <div key={idx} className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }} />
                <span>{item.name} ({item.value} calls)</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Bottom Performance matrix summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Provider Performance */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">LLM Gateways Performance Matrix</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">Average latencies and costs sorted by provider integration channels.</p>
          </div>

          <div className="flex flex-col gap-2 overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-white/5 text-neutral-500 pb-2">
                  <th className="pb-2">Gateway Channel</th>
                  <th className="pb-2">Total Queries</th>
                  <th className="pb-2">Success Rate</th>
                  <th className="pb-2 text-right">Avg Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {performanceBreakdown.providers.map((p, idx) => (
                  <tr key={idx} className="text-neutral-300">
                    <td className="py-2.5 font-semibold text-white capitalize">{p.name}</td>
                    <td className="py-2.5 font-mono">{p.requests} calls</td>
                    <td className="py-2.5 font-mono">
                      <span className={p.successRate > 90 ? 'text-emerald-400' : 'text-amber-400'}>
                        {p.successRate}%
                      </span>
                    </td>
                    <td className="py-2.5 text-right font-mono text-neutral-400">{p.avgLatency}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Top Models */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Most Utilized Model Nodes</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">Ranking model integrations by incoming prompt queries.</p>
          </div>

          <div className="flex flex-col gap-2 overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-white/5 text-neutral-500 pb-2">
                  <th className="pb-2">Model Node</th>
                  <th className="pb-2">Total Queries</th>
                  <th className="pb-2">Success Rate</th>
                  <th className="pb-2 text-right">Accumulated Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {performanceBreakdown.models.map((m, idx) => (
                  <tr key={idx} className="text-neutral-300">
                    <td className="py-2.5 font-semibold text-white font-mono text-[10px]">{m.name}</td>
                    <td className="py-2.5 font-mono">{m.requests} calls</td>
                    <td className="py-2.5 font-mono">
                      <span className={m.successRate > 90 ? 'text-emerald-400' : 'text-amber-400'}>
                        {m.successRate}%
                      </span>
                    </td>
                    <td className="py-2.5 text-right font-mono text-emerald-500">${m.cost.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Recent Inference Logs datatable */}
      <Card className="flex flex-col gap-4 mt-6">
        <div>
          <h4 className="font-bold text-white text-sm">Recent Inference logs</h4>
          <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Live trace queries processed by active routing channels.</p>
        </div>

        <div className="rounded-xl border border-white/5 overflow-hidden">
          <DataTable
            columns={columnsLogs}
            data={filteredUsage}
            isLoading={isLoading}
            pageSize={10}
            searchable={false}
          />
        </div>
      </Card>

      <InspectorDialog
        isOpen={showInspector}
        onClose={() => setShowInspector(false)}
        requestLog={selLogForInspect}
      />
    </div>
  );
}
