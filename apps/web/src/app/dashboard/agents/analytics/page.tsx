'use client';

import * as React from 'react';
import { AnalyticsCards, AnalyticsCharts } from '@/features/agents/components/analytics';
import { BarChart3, TrendingUp, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function AgentAnalyticsPage() {
  const [loading, setLoading] = React.useState(false);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 800);
  };

  const chartData = [
    { name: 'Mon', runs: 42, cost: 0.124, latency: 1250 },
    { name: 'Tue', runs: 58, cost: 0.186, latency: 1900 },
    { name: 'Wed', runs: 74, cost: 0.245, latency: 1400 },
    { name: 'Thu', runs: 65, cost: 0.219, latency: 1850 },
    { name: 'Fri', runs: 90, cost: 0.312, latency: 2200 },
    { name: 'Sat', runs: 30, cost: 0.088, latency: 980 },
    { name: 'Sun', runs: 28, cost: 0.076, latency: 1100 },
  ];

  const metrics = {
    totalRuns: 387,
    successRate: 98.4,
    avgLatency: 1540,
    totalCost: 1.25,
    totalTokens: 128400,
  };

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-white/5 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-violet-400" /> Platform Performance Analytics
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            Analyze historical pipeline throughput, model execution latency, and cumulative costs.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={handleRefresh}
          className="h-10 text-xs font-semibold gap-1.5 border-white/5 text-neutral-300 hover:text-white"
          isLoading={loading}
        >
          <RefreshCw className="w-3.5 h-3.5" /> Sync metrics
        </Button>
      </div>

      {/* Analytics KPI cards */}
      <AnalyticsCards metrics={metrics} />

      {/* Chart visual grids */}
      <AnalyticsCharts data={chartData} />
    </div>
  );
}
