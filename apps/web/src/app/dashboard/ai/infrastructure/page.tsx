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
  Server, Database, Activity, RefreshCw, Layers, ShieldAlert,
  Play, CheckCircle2, Clock, Trash2, Cpu, Sliders, HardDrive, BarChart2
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Mock chart data for cache and worker throughput stats
const CACHE_CHART_DATA = [
  { time: '10:00', hits: 120, misses: 10 },
  { time: '11:00', hits: 180, misses: 15 },
  { time: '12:00', hits: 240, misses: 25 },
  { time: '13:00', hits: 190, misses: 12 },
  { time: '14:00', hits: 310, misses: 18 },
  { time: '15:00', hits: 280, misses: 20 },
];

export default function InfrastructurePage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = React.useState<'overview' | 'cache' | 'workers' | 'queues' | 'scheduler'>('overview');

  // Queries
  const healthQuery = useQuery({
    queryKey: ['infra-health'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/infrastructure/health');
      return res.data;
    },
    refetchInterval: 15000,
  });

  const redisQuery = useQuery({
    queryKey: ['infra-redis'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/infrastructure/redis');
      return res.data;
    },
    refetchInterval: 10000,
  });

  const cacheQuery = useQuery({
    queryKey: ['infra-cache'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/infrastructure/cache');
      return res.data;
    },
    refetchInterval: 10000,
  });

  const workersQuery = useQuery({
    queryKey: ['infra-workers'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/infrastructure/workers');
      return res.data;
    },
    refetchInterval: 10000,
  });

  const jobsQuery = useQuery({
    queryKey: ['infra-jobs'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/infrastructure/jobs');
      return res.data || [];
    },
    refetchInterval: 5000,
  });

  const queuesQuery = useQuery({
    queryKey: ['infra-queues'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/infrastructure/queues');
      return res.data;
    },
    refetchInterval: 10000,
  });

  // Mutations
  const reconnectRedis = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/ai/infrastructure/redis/reconnect');
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['infra-redis'] });
      toast.success('Redis Reconnected', 'Successfully flushed and reinitialized connection pool.');
    },
  });

  const clearCache = useMutation({
    mutationFn: async (payload: { namespace?: string; org_id?: string }) => {
      const res = await apiClient.post('/ai/infrastructure/cache/clear', payload);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['infra-cache'] });
      toast.success('Cache Invalidation Complete', data.message || 'Cache cleared successfully.');
    },
  });

  const triggerJob = useMutation({
    mutationFn: async (taskName: string) => {
      const res = await apiClient.post('/ai/infrastructure/jobs/run', { task_name: taskName });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['infra-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['infra-workers'] });
      toast.success('Task Dispatched', 'Background worker task scheduled successfully.');
    },
  });

  const handleRefreshAll = () => {
    healthQuery.refetch();
    redisQuery.refetch();
    cacheQuery.refetch();
    workersQuery.refetch();
    jobsQuery.refetch();
    queuesQuery.refetch();
    toast.success('Metrics Refreshed', 'Successfully fetched live telemetry parameters.');
  };

  const health = healthQuery.data || { database: 'unknown', redis: 'unknown', latency_ms: 0, status: 'unknown' };
  const redis = redisQuery.data || { status: 'disconnected', latency_ms: 0.0, connected_clients: 0, used_memory_human: '0B', cluster_enabled: false, sentinel_enabled: false, connects_count: 0, errors_count: 0 };
  const cache = cacheQuery.data || { hits: 0, misses: 0, hit_ratio: 0.0, miss_ratio: 0.0, evictions: 0, cached_keys_count: 0 };
  const workers = workersQuery.data || { jobs: { total: 0, running: 0, failed: 0, completed: 0 }, worker_metrics: [], active_nodes_count: 0 };
  const jobs = jobsQuery.data || [];
  const queues = queuesQuery.data || { total_size: 0 };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-white/5 pb-4 gap-4">
        <PageHeader
          title="Infrastructure Management"
          description="Global monitoring console for Redis broker, cache layers, Celery beat schedules, and queue volumes."
          icon={<Server className="w-5 h-5 text-violet-400" />}
          badge={<Badge variant="violet">Platform Core</Badge>}
        />
        
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefreshAll}
          className="h-8 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" />
          Refresh Stats
        </Button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Database Status"
          value={health.database === 'healthy' ? 'ONLINE' : 'ERROR'}
          icon={<Database className="w-4 h-4 text-emerald-400" />}
          description="Postgres connection pool"
          isLoading={healthQuery.isLoading}
        />
        <StatCard
          title="Redis Broker"
          value={redis.status === 'connected' ? 'ONLINE' : 'ERROR'}
          icon={<Activity className="w-4 h-4 text-violet-400" />}
          description={`Latency: ${redis.latency_ms}ms`}
          isLoading={redisQuery.isLoading}
        />
        <StatCard
          title="Cache Keys Count"
          value={cache.cached_keys_count}
          icon={<Layers className="w-4 h-4 text-sky-400" />}
          description={`Hit Ratio: ${cache.hit_ratio}%`}
          isLoading={cacheQuery.isLoading}
        />
        <StatCard
          title="Queued Tasks"
          value={queues.total_size}
          icon={<HardDrive className="w-4 h-4 text-amber-400" />}
          description="Inference & sync requests"
          isLoading={queuesQuery.isLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="flex flex-col gap-2">
          {[
            { id: 'overview', label: 'Infrastructure Overview', icon: <Server className="w-4 h-4" /> },
            { id: 'cache', label: 'AI Cache Controls', icon: <Layers className="w-4 h-4" /> },
            { id: 'workers', label: 'Background Workers', icon: <Cpu className="w-4 h-4" /> },
            { id: 'queues', label: 'Message Queues', icon: <HardDrive className="w-4 h-4" /> },
            { id: 'scheduler', label: 'Schedules Timer', icon: <Sliders className="w-4 h-4" /> },
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
                <Card className="flex flex-col gap-6">
                  <div>
                    <h3 className="font-bold text-white text-sm">Redis Infrastructure</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Telemetry overview for broker connectivity metrics.</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col gap-2">
                      <span className="text-xs font-bold text-white">Pool Configuration</span>
                      <div className="flex flex-col gap-1 text-[11px] font-mono text-neutral-400 mt-2">
                        <div className="flex justify-between"><span>Sentinel Enabled:</span><span className="text-white">{redis.sentinel_enabled ? 'Yes' : 'No'}</span></div>
                        <div className="flex justify-between"><span>Cluster Enabled:</span><span className="text-white">{redis.cluster_enabled ? 'Yes' : 'No'}</span></div>
                        <div className="flex justify-between"><span>Total Connects:</span><span className="text-white">{redis.connects_count}</span></div>
                        <div className="flex justify-between"><span>Errors Caught:</span><span className="text-white text-rose-400">{redis.errors_count}</span></div>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col gap-2">
                      <span className="text-xs font-bold text-white">Memory & Connections</span>
                      <div className="flex flex-col gap-1 text-[11px] font-mono text-neutral-400 mt-2">
                        <div className="flex justify-between"><span>Used Memory:</span><span className="text-white">{redis.used_memory_human}</span></div>
                        <div className="flex justify-between"><span>Clients Connected:</span><span className="text-white">{redis.connected_clients}</span></div>
                        <div className="flex justify-between"><span>Socket Timeout:</span><span className="text-white">2.0s</span></div>
                        <div className="flex justify-between text-violet-400 font-bold">
                          <span>Reconnect Broker:</span>
                          <button 
                            disabled={reconnectRedis.isPending}
                            onClick={() => reconnectRedis.mutate()} 
                            className="hover:underline cursor-pointer"
                          >
                            Reconnect
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              )}

              {activeTab === 'cache' && (
                <Card className="flex flex-col gap-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-white text-sm">Cache Layers Control</h3>
                      <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Flush template metadata, vector index mappings, or execution logs cache.</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => clearCache.mutate({})}
                      disabled={clearCache.isPending}
                      className="h-8 border-rose-500/20 text-rose-400 bg-rose-950/10 hover:bg-rose-950/20"
                    >
                      <Trash2 className="w-3.5 h-3.5 mr-1" />
                      Flush All Cache
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-1">
                      <span className="text-[10px] text-neutral-500 font-mono">CACHE HITS</span>
                      <span className="text-xl font-mono font-bold text-white">{cache.hits}</span>
                    </div>
                    <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-1">
                      <span className="text-[10px] text-neutral-500 font-mono">CACHE MISSES</span>
                      <span className="text-xl font-mono font-bold text-white">{cache.misses}</span>
                    </div>
                    <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-1">
                      <span className="text-[10px] text-neutral-500 font-mono">EVICTIONS</span>
                      <span className="text-xl font-mono font-bold text-rose-400">{cache.evictions}</span>
                    </div>
                  </div>

                  <div className="h-48 w-full border border-white/5 rounded-xl p-3 bg-neutral-950/40">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={CACHE_CHART_DATA}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" />
                        <XAxis dataKey="time" stroke="#666" fontSize={10} />
                        <YAxis stroke="#666" fontSize={10} />
                        <Tooltip />
                        <Area type="monotone" dataKey="hits" stroke="#8884d8" fill="#8884d820" />
                        <Area type="monotone" dataKey="misses" stroke="#82ca9d" fill="#82ca9d20" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="flex flex-col gap-3">
                    <span className="text-xs font-bold text-white">Namespaces Invalidation</span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {['playground', 'prompt', 'routing', 'knowledge', 'organization'].map((ns) => (
                        <button
                          key={ns}
                          onClick={() => clearCache.mutate({ namespace: ns })}
                          disabled={clearCache.isPending}
                          className="px-3 py-2 border border-white/5 bg-neutral-950/40 text-[11px] font-mono text-neutral-400 hover:text-white rounded-lg text-left hover:border-violet-500/30 flex justify-between items-center transition-all"
                        >
                          <span>{ns}</span>
                          <Trash2 className="w-3 h-3 text-neutral-500" />
                        </button>
                      ))}
                    </div>
                  </div>
                </Card>
              )}

              {activeTab === 'workers' && (
                <Card className="flex flex-col gap-6">
                  <div>
                    <h3 className="font-bold text-white text-sm">Background Workers</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Trigger and inspect execution histories of background tasks.</p>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-0.5">
                      <span className="text-[9px] text-neutral-500 font-mono">RUNNING JOBS</span>
                      <span className="text-lg font-mono font-bold text-violet-400">{workers.jobs.running}</span>
                    </div>
                    <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-0.5">
                      <span className="text-[9px] text-neutral-500 font-mono">COMPLETED</span>
                      <span className="text-lg font-mono font-bold text-emerald-400">{workers.jobs.completed}</span>
                    </div>
                    <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-0.5">
                      <span className="text-[9px] text-neutral-500 font-mono">FAILED JOBS</span>
                      <span className="text-lg font-mono font-bold text-rose-400">{workers.jobs.failed}</span>
                    </div>
                    <div className="p-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-0.5">
                      <span className="text-[9px] text-neutral-500 font-mono">TOTAL EXECUTED</span>
                      <span className="text-lg font-mono font-bold text-white">{workers.jobs.total}</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-3">
                    <span className="text-xs font-bold text-white">Manual Tasks Trigger</span>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { name: 'worker.tasks.health_worker_task', label: 'Trigger Health Checks' },
                        { name: 'worker.tasks.model_sync_worker_task', label: 'Trigger Model Sync' },
                        { name: 'worker.tasks.cleanup_worker_task', label: 'Trigger Cache Cleanup' },
                      ].map((t) => (
                        <Button
                          key={t.name}
                          variant="outline"
                          size="sm"
                          onClick={() => triggerJob.mutate(t.name)}
                          disabled={triggerJob.isPending}
                          className="h-8 text-[11px] border-white/5 bg-neutral-900 hover:bg-neutral-800"
                        >
                          <Play className="w-3 h-3 mr-1" />
                          {t.label}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col gap-3">
                    <span className="text-xs font-bold text-white">Execution Logs History</span>
                    <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-1">
                      {jobs.length === 0 ? (
                        <span className="text-[11px] text-neutral-500">No background job log history found.</span>
                      ) : (
                        jobs.map((j: any) => (
                          <div key={j.id} className="p-3 border border-white/5 bg-neutral-950/40 rounded-xl flex items-center justify-between text-xs font-mono">
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-white">{j.name}</span>
                                <Badge variant={j.status === 'SUCCESS' ? 'emerald' : j.status === 'FAILURE' ? 'rose' : 'violet'}>
                                  {j.status}
                                </Badge>
                              </div>
                              <span className="text-[10px] text-neutral-500">Task ID: {j.task_id}</span>
                            </div>
                            <div className="flex flex-col items-end gap-1 text-[10px] text-neutral-500">
                              <span className="flex items-center"><Clock className="w-3 h-3 mr-1" /> {j.runtime ? `${j.runtime.toFixed(2)}s` : 'N/A'}</span>
                              <span>{new Date(j.created_at).toLocaleTimeString()}</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </Card>
              )}

              {activeTab === 'queues' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">Message Queues</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Real-time volume statistics for backend task pipelines.</p>
                  </div>

                  <div className="flex flex-col divide-y divide-white/5 mt-2">
                    {Object.entries(queues).map(([name, val]: [string, any]) => {
                      if (name === 'total_size') return null;
                      return (
                        <div key={name} className="py-3.5 flex items-center justify-between text-xs font-mono first:pt-0 last:pb-0">
                          <div className="flex flex-col gap-1">
                            <span className="font-sans font-bold text-white">{name}</span>
                            <span className="text-[10px] text-neutral-500">Total Processed: {val.processed_count}</span>
                          </div>
                          <Badge variant={val.size > 0 ? 'violet' : 'outline'}>
                            {val.size} pending
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {activeTab === 'scheduler' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">Celery Beat Scheduler</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Beat cron tasks schedules details.</p>
                  </div>

                  <div className="flex flex-col gap-3 mt-2">
                    {[
                      { name: 'provider-health-check-every-minute', task: 'worker.tasks.health_worker_task', schedule: 'Every 60s' },
                      { name: 'model-sync-every-day', task: 'worker.tasks.model_sync_worker_task', schedule: 'Daily at midnight' },
                      { name: 'cache-cleanup-every-hour', task: 'worker.tasks.cleanup_worker_task', schedule: 'Hourly' },
                      { name: 'usage-aggregation-every-hour', task: 'worker.tasks.usage_worker_task', schedule: 'Hourly' },
                      { name: 'cost-aggregation-every-day', task: 'worker.tasks.cost_worker_task', schedule: 'Daily at 1:00 AM' },
                    ].map((s) => (
                      <div key={s.name} className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs font-mono">
                        <div className="flex flex-col gap-1">
                          <span className="font-sans font-bold text-white">{s.name}</span>
                          <span className="text-[10px] text-neutral-500">{s.task}</span>
                        </div>
                        <Badge variant="emerald">
                          {s.schedule}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
