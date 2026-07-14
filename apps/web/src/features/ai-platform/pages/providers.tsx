import * as React from 'react';
import { useProviders, useProviderHealth } from '../hooks';
import { ProviderCard } from '../components/provider-card';
import { FilterPanel } from '../components/filter-panel';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Cpu, CheckCircle, AlertTriangle, Shield, RefreshCw } from 'lucide-react';
import { useAIPlatformStore } from '../store/ai-platform';

export function ProvidersPage() {
  const { providers, isLoading, refetch } = useProviders();
  const { refreshAll } = useProviderHealth();
  const { searchQuery, selectedProvider } = useAIPlatformStore();

  const handleSyncAll = async () => {
    await refreshAll.mutateAsync();
    refetch();
  };

  const filteredProviders = React.useMemo(() => {
    return providers.filter((p) => {
      // Filter by selected provider key
      if (selectedProvider && p.key !== selectedProvider) return false;
      // Filter by search query
      if (searchQuery) {
        return p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
               p.key.toLowerCase().includes(searchQuery.toLowerCase());
      }
      return true;
    });
  }, [providers, selectedProvider, searchQuery]);

  // Aggregate stats
  const totalCount = providers.length;
  const healthyCount = providers.filter((p) => p.isHealthy).length;
  const offlineCount = totalCount - healthyCount;
  const totalCost = providers.reduce((sum, p) => sum + p.cost, 0);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="AI Providers"
        description="Configure and monitor latency, connection states, health logs, and streaming throughput for integrated AI model routing endpoints."
        icon={<Cpu className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">{providers.length} Registered</Badge>}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncAll}
            disabled={isLoading || refreshAll.isPending}
            className="h-9 gap-1.5 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshAll.isPending ? 'animate-spin' : ''}`} />
            Sync Gateway State
          </Button>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Connections"
          value={totalCount}
          icon={<Cpu className="w-4 h-4 text-violet-400" />}
          description="Integrated provider channels"
          isLoading={isLoading}
        />
        <StatCard
          title="Healthy Standby"
          value={healthyCount}
          icon={<CheckCircle className="w-4 h-4 text-emerald-400" />}
          iconColor="text-emerald-400"
          change={totalCount ? `${Math.round((healthyCount / totalCount) * 100)}%` : undefined}
          isPositive
          description="Endpoints passing pings"
          isLoading={isLoading}
        />
        <StatCard
          title="Failing Connections"
          value={offlineCount}
          icon={<AlertTriangle className="w-4 h-4 text-rose-400" />}
          iconColor="text-rose-400"
          description="Endpoints failing checks"
          isLoading={isLoading}
        />
        <StatCard
          title="Total Gateway Cost"
          value={`$${totalCost.toFixed(3)}`}
          icon={<Shield className="w-4 h-4 text-amber-400" />}
          description="Accumulated session cost"
          isLoading={isLoading}
        />
      </div>

      {/* Filter and settings */}
      <FilterPanel showModelSelector={false} onRefresh={refetch} />

      {/* Providers Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-64 rounded-2xl border border-white/5 bg-neutral-900/20 animate-pulse" />
          ))}
        </div>
      ) : filteredProviders.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProviders.map((p, idx) => (
            <ProviderCard key={p.key} provider={p} delay={idx * 0.04} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center text-center py-20 border border-dashed border-white/5 rounded-2xl bg-neutral-950/20">
          <Cpu className="w-8 h-8 text-neutral-600 mb-3" />
          <h3 className="font-bold text-white text-sm">No Providers Found</h3>
          <p className="text-xs text-neutral-500 max-w-xs mt-1">
            Try adjusting your search criteria or register keys in AI settings to activate additional channels.
          </p>
        </div>
      )}
    </div>
  );
}
