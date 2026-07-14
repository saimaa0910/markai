import * as React from 'react';
import { usePromptAnalytics } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Card } from '@eaimos/ui';
import { BarChart3, TrendingUp, Clock, Cpu, Activity } from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend 
} from 'recharts';

export function AnalyticsPage() {
  const { stats } = usePromptAnalytics();

  const chartsData = React.useMemo(() => {
    return [
      { month: 'May', executions: 2200, cost: 0.85, latency: 250 },
      { month: 'Jun', executions: 3400, cost: 1.25, latency: 235 },
      { month: 'Jul', executions: 5100, cost: 1.95, latency: 240 },
    ];
  }, []);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Prompt Performance Analytics"
        description="Inspect execution cost allocations, prompt latencies, and category distribution percentages."
        icon={<BarChart3 className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Prompt telemetry</Badge>}
      />

      {/* Grid view charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Executions analytics */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Monthly Executions Volume</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Aggregated query allocations mapped monthly.</p>
          </div>

          <div className="h-[220px] w-full mt-2 text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="execGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" stroke="#525252" fontSize={9} tickLine={false} />
                <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                <Tooltip />
                <Area type="monotone" dataKey="executions" stroke="#8b5cf6" strokeWidth={2} fill="url(#execGrad)" name="Executions" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Latency analytics */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Response Latency Trends</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Latency checks mapped over time.</p>
          </div>

          <div className="h-[220px] w-full mt-2 text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" stroke="#525252" fontSize={9} tickLine={false} />
                <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                <Tooltip />
                <Bar dataKey="latency" fill="#10b981" radius={4} name="Latency (ms)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

      </div>

      {/* Categories listings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Prompt Categories breakdown</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">Summary of prompt templates grouped by category tags.</p>
          </div>

          <div className="flex flex-col gap-3 mt-1">
            {stats.categoriesBreakdown.map((cat: any) => (
              <div 
                key={cat.name} 
                className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs font-mono"
              >
                <span className="font-sans font-bold text-white text-sm capitalize">{cat.name}</span>
                <Badge variant="violet">{cat.value} templates</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
export { BarChart3 };
export type { TrendingUp, Clock, Cpu, Activity };
