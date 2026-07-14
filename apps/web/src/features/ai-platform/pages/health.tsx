import * as React from 'react';
import { useProviders, useProviderLogs } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  Activity, ShieldCheck, ShieldAlert, RefreshCw, Zap, 
  Clock, AlertTriangle, AlertCircle, Play, ServerCrash 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

interface IncidentLog {
  id: string;
  provider: string;
  timestamp: string;
  type: string;
  message: string;
  resolved: boolean;
}

const MOCK_INCIDENTS: IncidentLog[] = [
  {
    id: 'inc-1',
    provider: 'groq',
    timestamp: '2026-07-14T08:30:00Z',
    type: 'Rate Limit Exhausted',
    message: 'HTTP 429 received on llama3 inference node. Automatic fallback router redirected traffic to openai.',
    resolved: true,
  },
  {
    id: 'inc-2',
    provider: 'anthropic',
    timestamp: '2026-07-13T22:15:00Z',
    type: 'High Latency Spike',
    message: 'Average response latency exceeded 3200ms threshold on claude-3-5-sonnet.',
    resolved: true,
  },
  {
    id: 'inc-3',
    provider: 'google',
    timestamp: '2026-07-14T10:12:00Z',
    type: 'Network Handshake Fail',
    message: 'Connection timed out to gemini-1.5-flash API endpoint. Gateway retrying with fallback targets.',
    resolved: false,
  },
];

export function HealthPage() {
  const { providers, isLoading, refetch } = useProviders();
  const [incidents, setIncidents] = React.useState<IncidentLog[]>(MOCK_INCIDENTS);
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    await new Promise((resolve) => setTimeout(resolve, 800));
    setIsRefreshing(false);
    toast.success('Live Monitoring Refreshed', 'Handshake logs updated in real time.');
  };

  const handleResolveIncident = (id: string) => {
    setIncidents(
      incidents.map((inc) => (inc.id === id ? { ...inc, resolved: true } : inc))
    );
    toast.success('Incident Resolved', 'Marked target outage log as resolved.');
  };

  // Aggregated general stats
  const stats = React.useMemo(() => {
    if (!providers.length) {
      return { successRate: 100, avgLatency: 0, activeCount: 0 };
    }
    const successRate = Math.round(
      providers.reduce((sum, p) => sum + (p.isHealthy ? 100 : 0), 0) / providers.length
    );
    const avgLatency = Math.round(
      providers.reduce((sum, p) => sum + p.latency, 0) / providers.length
    );
    const activeCount = providers.filter((p) => p.isHealthy).length;
    return { successRate, avgLatency, activeCount };
  }, [providers]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Header with actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-white/5 pb-4 gap-4">
        <PageHeader
          title="Provider Health Center"
          description="Live infrastructure gateway monitor tracking error exception ratios, retry occurrences, and active incident workflows."
          icon={<Activity className="w-5 h-5 text-violet-400" />}
          badge={<Badge variant="violet">Live monitoring</Badge>}
        />
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="h-8 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
            disabled={isRefreshing}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Monitor
          </Button>
        </div>
      </div>

      {/* KPI Stats overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Gateways"
          value={`${stats.activeCount} / ${providers.length}`}
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
          description="Inference endpoints active"
          isLoading={isLoading}
        />
        <StatCard
          title="Overall Success Rate"
          value={`${stats.successRate}%`}
          icon={<Activity className="w-4 h-4 text-emerald-400" />}
          description="Passing uptime connection tests"
          isLoading={isLoading}
        />
        <StatCard
          title="Average Latency Overhead"
          value={`${stats.avgLatency}ms`}
          icon={<Zap className="w-4 h-4 text-amber-400" />}
          description="Gateway request roundtrip"
          isLoading={isLoading}
        />
        <StatCard
          title="Open Incidents"
          value={incidents.filter((i) => !i.resolved).length}
          icon={<ServerCrash className="w-4 h-4 text-rose-400" />}
          description="Pending server timeouts"
          isLoading={isLoading}
        />
      </div>

      {/* Main grids layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: LIVE PROVIDERS LIST */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Live Endpoint Gateways</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Real-time status check results for registered platform gateways.</p>
            </div>

            <div className="flex flex-col gap-3">
              {providers.map((p) => {
                // Mock historical timeline blocks (20 check pulses)
                const timeline = Array.from({ length: 20 }, (_, idx) => {
                  if (idx === 18 && p.key === 'google') return 'failed';
                  if (idx === 5 && p.key === 'groq') return 'warning';
                  return 'success';
                });

                return (
                  <div 
                    key={p.key} 
                    className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all hover:border-white/10"
                  >
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${p.isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500 animate-pulse'}`} />
                        <span className="text-xs font-bold text-white uppercase tracking-wider">{p.name}</span>
                        <Badge variant={p.isHealthy ? 'emerald' : 'rose'} size="sm">
                          {p.isHealthy ? 'Operational' : 'Degraded'}
                        </Badge>
                      </div>
                      
                      {/* Check timeline dots */}
                      <div className="flex items-center gap-1">
                        {timeline.map((state, idx) => (
                          <div 
                            key={idx}
                            className={`w-2 h-5 rounded-sm ${
                              state === 'success' 
                                ? 'bg-emerald-500/25 hover:bg-emerald-400' 
                                : state === 'warning'
                                ? 'bg-amber-500/30 hover:bg-amber-400'
                                : 'bg-rose-500/30 hover:bg-rose-400'
                            } transition-colors`}
                            title={`Ping test #${idx + 1}: ${state}`}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Stats metrics */}
                    <div className="flex items-center gap-6 text-[11px] font-mono shrink-0">
                      <div className="flex flex-col">
                        <span className="text-neutral-500">Latency</span>
                        <span className="text-white font-bold">{p.latency}ms</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-neutral-500">Retry Rate</span>
                        <span className="text-neutral-300">{(p.errorCount * 0.4).toFixed(1)}%</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-neutral-500">Success</span>
                        <span className="text-emerald-400 font-bold">{p.isHealthy ? '100%' : '88%'}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* RIGHT COLUMN: RECENT INCIDENTS TIMELINE */}
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Active Incident Timeline</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Logs recording outages, latency exceptions, and gateway failovers.</p>
            </div>

            <div className="flex flex-col gap-3">
              {incidents.map((inc) => (
                <div 
                  key={inc.id} 
                  className={`p-3 rounded-lg border flex flex-col gap-2 ${
                    inc.resolved 
                      ? 'border-white/5 bg-neutral-950/20' 
                      : 'border-rose-500/10 bg-rose-500/5'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      {inc.resolved ? (
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-400 animate-bounce" />
                      )}
                      <span className="text-xs font-bold text-white">{inc.type}</span>
                    </div>
                    <span className="text-[9px] text-neutral-500 font-mono">
                      {new Date(inc.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <p className="text-[10px] text-neutral-400 leading-relaxed font-mono">
                    [{inc.provider.toUpperCase()}] {inc.message}
                  </p>

                  {!inc.resolved && (
                    <div className="flex justify-end pt-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolveIncident(inc.id)}
                        className="h-6 text-[9px] border-rose-500/20 text-rose-400 hover:bg-rose-500/10"
                      >
                        Acknowledge & Resolve
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
