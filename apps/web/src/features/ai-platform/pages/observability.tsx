'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, ShieldAlert, FileText, BarChart3, Clock, AlertTriangle, 
  RefreshCw, Terminal, Layers, Database, Cpu, HardDrive, CheckCircle2,
  AlertCircle, XCircle, Search, Filter, Info, Server, Mail, Slack, Webhook, Zap
} from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, BarChart, Bar, Legend, PieChart, Pie, Cell 
} from 'recharts';

import { useObservabilityStore } from '@/store/observability';
import { 
  useObservabilityHealth, useObservabilityTraces, useObservabilityLogs, 
  useObservabilityIncidents, useObservabilityAlerts, useObservabilityPerformance, 
  useObservabilityLive, useTestAlertMutation 
} from '../hooks/useObservability';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { toast } from '@/components/ui/toast';

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

export function ObservabilityPage() {
  const { 
    activeTab, setActiveTab, searchQuery, setSearchQuery, 
    levelFilter, setLevelFilter, selectedTraceId, setSelectedTraceId,
    selectedTimeframeDays, setSelectedTimeframeDays
  } = useObservabilityStore();

  const [isRefreshing, setIsRefreshing] = React.useState(false);

  // Queries
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useObservabilityHealth();
  const { data: live, isLoading: liveLoading, refetch: refetchLive } = useObservabilityLive();
  const { data: performance, isLoading: perfLoading, refetch: refetchPerf } = useObservabilityPerformance(selectedTimeframeDays);
  const { data: traces = [], isLoading: tracesLoading, refetch: refetchTraces } = useObservabilityTraces({
    trace_id: searchQuery.length === 32 || searchQuery.length === 64 ? searchQuery : undefined,
    name: searchQuery.length > 2 && searchQuery.length < 32 ? searchQuery : undefined
  });
  const { data: logs = [], isLoading: logsLoading, refetch: refetchLogs } = useObservabilityLogs({
    search: searchQuery.length > 2 ? searchQuery : undefined,
    level: levelFilter
  });
  const { data: incidents = [], refetch: refetchIncidents } = useObservabilityIncidents();
  const { data: alerts = [], refetch: refetchAlerts } = useObservabilityAlerts();

  // Mutations
  const testAlertMutation = useTestAlertMutation();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([
      refetchHealth(),
      refetchLive(),
      refetchPerf(),
      refetchTraces(),
      refetchLogs(),
      refetchIncidents(),
      refetchAlerts()
    ]);
    setIsRefreshing(false);
    toast.success('Observability Data Refreshed', 'Telemetry nodes checked successfully.');
  };

  const handleTriggerTestAlert = async (severity: string) => {
    try {
      const res = await testAlertMutation.mutateAsync(severity);
      toast.success(
        'Simulated Alert Fired', 
        `Test dispatch resolved on channels: ${res.channels}`
      );
    } catch (e) {
      toast.error('Trigger Failed', 'Failed to execute simulated alert dispatch.');
    }
  };

  const activeIncidentsCount = live?.active_incidents?.length || 0;

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12 text-white">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-white/5 pb-4 gap-4">
        <PageHeader
          title="Enterprise Observability Center"
          description="Central operations control detailing request telemetry traces, structured logs indices, active alerts, and queue status."
          icon={<Activity className="w-5 h-5 text-violet-400" />}
          badge={<Badge variant="violet">Enterprise grade</Badge>}
        />
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="h-8 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
            disabled={isRefreshing}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </Button>
        </div>
      </div>

      {/* Primary KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Telemetry Uptime"
          value={health?.status?.toUpperCase() || 'HEALTHY'}
          icon={<Server className="w-4 h-4 text-emerald-400" />}
          description="Ecosystem health handshake OK"
          isLoading={healthLoading}
        />
        <StatCard
          title="Request Latency (P90)"
          value={`${performance?.summary?.p90_ms || live?.traffic_5m?.avg_latency_ms || 0} ms`}
          icon={<Clock className="w-4 h-4 text-violet-400" />}
          description="Gateway round-trip evaluation"
          isLoading={perfLoading || liveLoading}
        />
        <StatCard
          title="Active Incidents"
          value={`${activeIncidentsCount}`}
          icon={<ShieldAlert className="w-4 h-4 text-red-400" />}
          description="Unresolved failover exceptions"
          isLoading={liveLoading}
        />
        <StatCard
          title="Live Traffic (5m)"
          value={`${live?.traffic_5m?.requests_count || 0}`}
          icon={<Zap className="w-4 h-4 text-amber-400" />}
          description={`${live?.traffic_5m?.throughput_rpm || 0.0} requests per min`}
          isLoading={liveLoading}
        />
      </div>

      {/* Tabs navigation */}
      <div className="flex border-b border-white/5 gap-1 overflow-x-auto pb-px">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'metrics', label: 'Metrics', icon: BarChart3 },
          { id: 'logs', label: 'Structured Logs', icon: FileText },
          { id: 'tracing', label: 'Tracing Spans', icon: Layers },
          { id: 'performance', label: 'Performance Analytics', icon: Clock },
          { id: 'incidents', label: 'Incidents & Alerts', icon: AlertTriangle }
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-violet-500 text-violet-400 bg-violet-500/5'
                  : 'border-transparent text-neutral-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="min-h-[500px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
          >
            {/* OVERVIEW PANEL */}
            {activeTab === 'overview' && (
              <div className="flex flex-col gap-6">
                {/* Health Grids */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {health?.components && Object.entries(health.components).map(([comp, status]) => {
                    const isOk = status === 'healthy';
                    const isWarning = status === 'warning';
                    return (
                      <Card key={comp} className="border-white/5 bg-neutral-950/40 p-4 flex flex-col gap-2 items-center text-center justify-center">
                        <span className="text-xs font-semibold text-neutral-400 capitalize">{comp}</span>
                        {isOk ? (
                          <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                        ) : isWarning ? (
                          <AlertCircle className="w-8 h-8 text-amber-500" />
                        ) : (
                          <XCircle className="w-8 h-8 text-red-500" />
                        )}
                        <span className={`text-xs font-bold ${isOk ? 'text-emerald-400' : isWarning ? 'text-amber-400' : 'text-red-400'}`}>
                          {status.toUpperCase()}
                        </span>
                      </Card>
                    );
                  })}
                </div>

                {/* Dashboard Chart and Info Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Traffic Chart */}
                  <Card className="lg:col-span-2 border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                    <div>
                      <h3 className="text-sm font-bold text-white">Live Execution Throughput</h3>
                      <p className="text-xs text-neutral-400">Real-time requests flow through gateway pipelines.</p>
                    </div>
                    <div className="h-[250px] w-full">
                      {performance?.provider_comparison && performance.provider_comparison.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={performance.provider_comparison}>
                            <defs>
                              <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                            <XAxis dataKey="model" stroke="#737373" fontSize={10} />
                            <YAxis stroke="#737373" fontSize={10} />
                            <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#262626' }} />
                            <Area type="monotone" dataKey="requests_count" name="Requests count" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorRequests)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center text-xs text-neutral-400">
                          Waiting for live traffic data...
                        </div>
                      )}
                    </div>
                  </Card>

                  {/* System State Overview */}
                  <Card className="border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                    <h3 className="text-sm font-bold text-white">Infrastructure Resources</h3>
                    <div className="flex flex-col gap-3.5">
                      <div className="flex justify-between items-center border-b border-white/5 pb-2">
                        <div className="flex items-center gap-2">
                          <Database className="w-4 h-4 text-blue-400" />
                          <span className="text-xs font-semibold text-neutral-300">Redis Memory</span>
                        </div>
                        <span className="text-xs font-bold text-white">{live?.redis?.used_memory || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between items-center border-b border-white/5 pb-2">
                        <div className="flex items-center gap-2">
                          <Cpu className="w-4 h-4 text-violet-400" />
                          <span className="text-xs font-semibold text-neutral-300">Celery Workers</span>
                        </div>
                        <span className="text-xs font-bold text-white">{live?.workers?.active_workers_count || 0} active</span>
                      </div>
                      <div className="flex justify-between items-center border-b border-white/5 pb-2">
                        <div className="flex items-center gap-2">
                          <HardDrive className="w-4 h-4 text-emerald-400" />
                          <span className="text-xs font-semibold text-neutral-300">Redis Connections</span>
                        </div>
                        <span className="text-xs font-bold text-white">{live?.redis?.connections || 0}</span>
                      </div>
                    </div>

                    {/* Active Incidents listing */}
                    <div className="flex flex-col gap-2 mt-2">
                      <h4 className="text-xs font-bold text-neutral-400">Active Incidents ({activeIncidentsCount})</h4>
                      {activeIncidentsCount > 0 ? (
                        <div className="flex flex-col gap-2 max-h-[120px] overflow-y-auto pr-1">
                          {live?.active_incidents?.map((inc) => (
                            <div key={inc.id} className="flex flex-col border border-red-500/20 bg-red-500/5 p-2 rounded gap-1">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-red-400 uppercase">{inc.component} failure</span>
                                <span className="text-[9px] text-neutral-400">{new Date(inc.start_time).toLocaleTimeString()}</span>
                              </div>
                              <span className="text-[11px] text-neutral-200 line-clamp-1">{inc.root_cause}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="flex items-center justify-center py-4 bg-emerald-500/5 border border-emerald-500/10 rounded">
                          <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5" /> No active incidents
                          </span>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {/* METRICS PANEL */}
            {activeTab === 'metrics' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Cache Performance */}
                <Card className="border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                  <h3 className="text-sm font-bold text-white">Cache Performance Ratio</h3>
                  <div className="h-[200px] flex items-center justify-center">
                    {performance?.cache_performance ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Cache Hits', value: performance.cache_performance.hits },
                              { name: 'Cache Misses', value: performance.cache_performance.misses }
                            ]}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            <Cell fill="#8b5cf6" />
                            <Cell fill="#ef4444" />
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="text-xs text-neutral-400">Gathering cache statistics...</div>
                    )}
                  </div>
                </Card>

                {/* Active Queues status */}
                <Card className="border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                  <h3 className="text-sm font-bold text-white">Celery Queues Message Depth</h3>
                  <div className="h-[200px] flex flex-col justify-center">
                    {live?.queues && Object.keys(live.queues).length > 0 ? (
                      <div className="flex flex-col gap-3">
                        {Object.entries(live.queues).map(([name, qInfo]: [string, any]) => (
                          <div key={name} className="flex flex-col gap-1.5">
                            <div className="flex justify-between items-center">
                              <span className="text-xs text-neutral-300 font-semibold">{name} queue</span>
                              <span className="text-xs text-white font-bold">{qInfo.size || 0} messages pending</span>
                            </div>
                            <div className="w-full bg-neutral-900 rounded-full h-2">
                              <div 
                                className="bg-violet-500 h-2 rounded-full transition-all" 
                                style={{ width: `${Math.min(100, ((qInfo.size || 0) * 10))}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-neutral-400 text-center">No active queues monitored.</div>
                    )}
                  </div>
                </Card>

                {/* Comparative request count */}
                <Card className="md:col-span-2 border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                  <h3 className="text-sm font-bold text-white">Provider Performance & Call Load</h3>
                  <div className="h-[250px]">
                    {performance?.provider_comparison && performance.provider_comparison.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={performance.provider_comparison}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                          <XAxis dataKey="model" stroke="#737373" fontSize={10} />
                          <YAxis stroke="#737373" fontSize={10} />
                          <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#262626' }} />
                          <Legend />
                          <Bar dataKey="requests_count" name="Total Calls" fill="#3b82f6" />
                          <Bar dataKey="avg_latency_ms" name="Avg Latency (ms)" fill="#8b5cf6" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-neutral-400">
                        No metric load statistics available.
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            )}

            {/* STRUCTURED LOGS PANEL */}
            {activeTab === 'logs' && (
              <Card className="border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white">Structured Log Audit</h3>
                    <p className="text-xs text-neutral-400">Consolidated list of backend execution event logs.</p>
                  </div>
                  
                  {/* Filters */}
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-neutral-400 absolute left-2.5 top-2.5" />
                      <input
                        type="text"
                        placeholder="Search logs message..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="bg-neutral-900 border border-white/5 rounded text-xs pl-8 pr-3 py-1.5 focus:outline-none focus:border-violet-500 text-white w-[200px]"
                      />
                    </div>
                    
                    <select
                      value={levelFilter}
                      onChange={(e) => setLevelFilter(e.target.value)}
                      className="bg-neutral-900 border border-white/5 rounded text-xs px-2.5 py-1.5 focus:outline-none focus:border-violet-500 text-white"
                    >
                      <option value="ALL">ALL LEVELS</option>
                      <option value="INFO">INFO</option>
                      <option value="WARNING">WARNING</option>
                      <option value="ERROR">ERROR</option>
                    </select>
                  </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-white/5 text-neutral-400">
                        <th className="py-2 font-bold">Timestamp</th>
                        <th className="py-2 font-bold">Level</th>
                        <th className="py-2 font-bold">Logger</th>
                        <th className="py-2 font-bold">Message</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logsLoading ? (
                        <tr>
                          <td colSpan={4} className="py-8 text-center text-neutral-400">
                            Loading logs registry...
                          </td>
                        </tr>
                      ) : logs.length > 0 ? (
                        logs.map((log) => {
                          const isErr = log.level === 'ERROR';
                          const isWarn = log.level === 'WARNING';
                          return (
                            <React.Fragment key={log.id}>
                              <tr className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                <td className="py-3 text-neutral-400 whitespace-nowrap">
                                  {new Date(log.timestamp).toLocaleString()}
                                </td>
                                <td className="py-3 whitespace-nowrap">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                    isErr ? 'bg-red-500/10 text-red-400' : isWarn ? 'bg-amber-500/10 text-amber-400' : 'bg-blue-500/10 text-blue-400'
                                  }`}>
                                    {log.level}
                                  </span>
                                </td>
                                <td className="py-3 text-neutral-300 font-semibold max-w-[120px] truncate">
                                  {log.logger}
                                </td>
                                <td className="py-3 text-neutral-200">
                                  <div className="flex flex-col gap-1">
                                    <span>{log.message}</span>
                                    {log.payload && Object.keys(log.payload).length > 0 && (
                                      <pre className="text-[10px] text-neutral-400 bg-neutral-900/50 p-2 rounded border border-white/5 max-w-[800px] overflow-x-auto">
                                        {JSON.stringify(log.payload, null, 2)}
                                      </pre>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            </React.Fragment>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={4} className="py-8 text-center text-neutral-400">
                            No logs found matching filter criteria.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {/* TRACING PANEL */}
            {activeTab === 'tracing' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Traces List */}
                <Card className="lg:col-span-1 border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                  <h3 className="text-sm font-bold text-white">Gateway Request Spans</h3>
                  <div className="flex flex-col gap-2 max-h-[450px] overflow-y-auto pr-1">
                    {tracesLoading ? (
                      <div className="text-xs text-neutral-400 py-8 text-center">Loading traces...</div>
                    ) : traces.length > 0 ? (
                      traces.map((trace) => {
                        const isErr = trace.status === 'error';
                        const isSelected = selectedTraceId === trace.trace_id;
                        return (
                          <button
                            key={trace.id}
                            onClick={() => setSelectedTraceId(trace.trace_id)}
                            className={`flex flex-col border p-3 rounded text-left gap-1.5 transition-all ${
                              isSelected 
                                ? 'border-violet-500 bg-violet-500/10' 
                                : 'border-white/5 bg-neutral-900/50 hover:bg-neutral-900'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-white truncate max-w-[150px]">{trace.name}</span>
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                isErr ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400'
                              }`}>
                                {trace.status.toUpperCase()}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-[10px] text-neutral-400">
                              <span>Trace ID: {trace.trace_id.slice(0, 8)}...</span>
                              <span className="font-semibold text-neutral-300">{trace.duration_ms} ms</span>
                            </div>
                          </button>
                        );
                      })
                    ) : (
                      <div className="text-xs text-neutral-400 py-8 text-center">No trace spans collected yet.</div>
                    )}
                  </div>
                </Card>

                {/* Waterfall Visualizer */}
                <Card className="lg:col-span-2 border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                  <h3 className="text-sm font-bold text-white">Trace Span Waterfall Visualizer</h3>
                  
                  {selectedTraceId ? (
                    (() => {
                      const activeTrace = traces.find(t => t.trace_id === selectedTraceId);
                      if (!activeTrace) return <div className="text-xs text-neutral-400 py-8 text-center">Trace details not found.</div>;
                      
                      // Mock child spans to create waterfall visualization representing Gateway -> Security -> Router -> Adapter
                      const startTs = new Date(activeTrace.start_time).getTime();
                      const endTs = new Date(activeTrace.end_time).getTime();
                      const totalDur = endTs - startTs || activeTrace.duration_ms || 1;
                      
                      const childSpans = [
                        { name: 'Gateway Auth Isolation Check', startOffset: 0, duration: Math.round(totalDur * 0.05) },
                        { name: 'AI Security input_scan', startOffset: Math.round(totalDur * 0.05), duration: Math.round(totalDur * 0.15) },
                        { name: 'ModelRouter matching', startOffset: Math.round(totalDur * 0.20), duration: Math.round(totalDur * 0.10) },
                        { name: `adapter.${activeTrace.attributes?.provider || 'provider'}.chat_completion`, startOffset: Math.round(totalDur * 0.30), duration: Math.round(totalDur * 0.60) },
                        { name: 'AI Security output_scan', startOffset: Math.round(totalDur * 0.90), duration: Math.round(totalDur * 0.10) }
                      ];

                      return (
                        <div className="flex flex-col gap-4">
                          {/* Span details metadata */}
                          <div className="bg-neutral-900/50 border border-white/5 p-3 rounded flex flex-col gap-2">
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-violet-400">{activeTrace.name}</span>
                              <span className="text-xs text-neutral-300 font-semibold">{activeTrace.duration_ms} ms</span>
                            </div>
                            <span className="text-[10px] text-neutral-400">Trace UUID: {activeTrace.trace_id}</span>
                            {activeTrace.attributes && (
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 border-t border-white/5 pt-2 mt-1">
                                {Object.entries(activeTrace.attributes).map(([key, val]) => (
                                  <div key={key} className="flex flex-col">
                                    <span className="text-[9px] text-neutral-400 uppercase">{key}</span>
                                    <span className="text-xs text-neutral-200 font-bold">{String(val)}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Waterfall Bars */}
                          <div className="flex flex-col gap-3.5 mt-2">
                            {childSpans.map((span, idx) => {
                              const leftPct = (span.startOffset / totalDur) * 100;
                              const widthPct = (span.duration / totalDur) * 100;
                              return (
                                <div key={idx} className="grid grid-cols-3 items-center gap-4">
                                  <span className="col-span-1 text-[11px] text-neutral-300 font-semibold truncate">{span.name}</span>
                                  <div className="col-span-2 bg-neutral-900/80 h-4 rounded relative overflow-hidden">
                                    <div 
                                      className="bg-violet-500 h-full rounded transition-all duration-300 flex items-center justify-end pr-1 text-[8px] font-bold text-white" 
                                      style={{ left: `${leftPct}%`, width: `${Math.max(4, widthPct)}%`, position: 'absolute' }}
                                    >
                                      {span.duration}ms
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="h-[200px] border border-dashed border-white/10 rounded flex flex-col items-center justify-center text-center gap-2 text-xs text-neutral-400">
                      <Layers className="w-8 h-8 text-neutral-500" />
                      Select a request span from the left to visualize the waterfall trace execution path.
                    </div>
                  )}
                </Card>
              </div>
            )}

            {/* PERFORMANCE PANEL */}
            {activeTab === 'performance' && (
              <div className="flex flex-col gap-6">
                {/* Timeframe Select */}
                <div className="flex items-center gap-2 bg-neutral-950/40 border border-white/5 p-3 rounded justify-between">
                  <div className="flex items-center gap-2">
                    <Info className="w-4 h-4 text-violet-400" />
                    <span className="text-xs text-neutral-300">Compare latency percentiles across historical calls.</span>
                  </div>
                  <select
                    value={selectedTimeframeDays}
                    onChange={(e) => setSelectedTimeframeDays(Number(e.target.value))}
                    className="bg-neutral-900 border border-white/5 rounded text-xs px-2.5 py-1.5 focus:outline-none text-white"
                  >
                    <option value={7}>LAST 7 DAYS</option>
                    <option value={30}>LAST 30 DAYS</option>
                    <option value={90}>LAST 90 DAYS</option>
                  </select>
                </div>

                {/* Percentiles stats grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Percentile distribution card */}
                  <Card className="border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                    <h3 className="text-sm font-bold text-white">Latency Distribution Curves</h3>
                    <div className="flex flex-col gap-3">
                      {[
                        { label: 'P50 (Median)', val: performance?.summary?.p50_ms || 0, desc: '50% of requests are faster than this' },
                        { label: 'P90 (Typical)', val: performance?.summary?.p90_ms || 0, desc: '90% of requests are faster than this' },
                        { label: 'P95 (Slow)', val: performance?.summary?.p95_ms || 0, desc: '95% of requests are faster than this' },
                        { label: 'P99 (Extreme)', val: performance?.summary?.p99_ms || 0, desc: '99% of requests are faster than this' }
                      ].map((p, idx) => (
                        <div key={idx} className="flex justify-between items-center border-b border-white/5 pb-2">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-xs font-semibold text-white">{p.label}</span>
                            <span className="text-[9px] text-neutral-400">{p.desc}</span>
                          </div>
                          <span className="text-sm font-bold text-violet-400">{p.val} ms</span>
                        </div>
                      ))}
                    </div>
                  </Card>

                  {/* Comparisons charts */}
                  <Card className="md:col-span-2 border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                    <h3 className="text-sm font-bold text-white">Aggregate Latency Comparison</h3>
                    <div className="h-[250px]">
                      {performance?.provider_comparison && performance.provider_comparison.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={performance.provider_comparison}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                            <XAxis dataKey="provider" stroke="#737373" fontSize={10} />
                            <YAxis stroke="#737373" fontSize={10} />
                            <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#262626' }} />
                            <Legend />
                            <Bar dataKey="avg_latency_ms" name="Average Latency (ms)" fill="#8b5cf6" />
                            <Bar dataKey="total_cost_usd" name="Accumulated Spend ($)" fill="#10b981" />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center text-xs text-neutral-400">
                          Waiting for latency comparison logs...
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {/* INCIDENTS & ALERTS PANEL */}
            {activeTab === 'incidents' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left panel: Trigger test actions */}
                <Card className="lg:col-span-1 border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                  <h3 className="text-sm font-bold text-white">Simulate Outage Events</h3>
                  <p className="text-xs text-neutral-400">
                    Use these options to trigger simulated incidents to verify notifications are active on Slack, Email, or Webhooks.
                  </p>
                  
                  <div className="flex flex-col gap-3 mt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTriggerTestAlert('warning')}
                      className="border-amber-500/20 bg-amber-500/5 hover:bg-amber-500/10 text-amber-400"
                    >
                      Trigger Test WARNING Alert
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTriggerTestAlert('critical')}
                      className="border-red-500/20 bg-red-500/5 hover:bg-red-500/10 text-red-400"
                    >
                      Trigger Test CRITICAL Alert
                    </Button>
                  </div>

                  <div className="border-t border-white/5 pt-4 mt-2">
                    <h4 className="text-xs font-bold text-neutral-300">Active Alert Dispatch channels:</h4>
                    <div className="flex items-center gap-4 mt-3 text-neutral-400">
                      <div className="flex items-center gap-1.5 text-xs">
                        <Slack className="w-4 h-4 text-pink-400" /> Slack
                      </div>
                      <div className="flex items-center gap-1.5 text-xs">
                        <Mail className="w-4 h-4 text-blue-400" /> Email
                      </div>
                      <div className="flex items-center gap-1.5 text-xs">
                        <Webhook className="w-4 h-4 text-violet-400" /> Webhook
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Right panel: Alerts Log */}
                <Card className="lg:col-span-2 border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4">
                  <h3 className="text-sm font-bold text-white">Alert Dispatch Audit History</h3>
                  <div className="overflow-y-auto max-h-[400px] pr-1">
                    {alerts.length > 0 ? (
                      <div className="flex flex-col gap-3">
                        {alerts.map((al) => {
                          const isCrit = al.severity === 'critical';
                          const isWarn = al.severity === 'warning';
                          const isSent = al.status === 'sent';
                          return (
                            <div key={al.id} className="border border-white/5 bg-neutral-900/40 p-3.5 rounded flex flex-col gap-2">
                              <div className="flex items-center justify-between">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  isCrit ? 'bg-red-500/10 text-red-400' : isWarn ? 'bg-amber-500/10 text-amber-400' : 'bg-blue-500/10 text-blue-400'
                                }`}>
                                  {al.alert_type}
                                </span>
                                <span className="text-[10px] text-neutral-400">
                                  {new Date(al.created_at).toLocaleString()}
                                </span>
                              </div>
                              <span className="text-xs text-neutral-200">{al.message}</span>
                              <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-1">
                                <span className="text-[9px] text-neutral-400">Channels: {al.channels}</span>
                                <span className={`text-[10px] font-bold ${isSent ? 'text-emerald-400' : 'text-red-400'}`}>
                                  {al.status.toUpperCase()}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-xs text-neutral-400 py-8 text-center">No alert dispatch logs available.</div>
                    )}
                  </div>
                </Card>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
