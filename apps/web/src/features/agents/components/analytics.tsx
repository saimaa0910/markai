'use client';

import * as React from 'react';
import { 
  BarChart, Bar, LineChart, Line, AreaChart, Area, 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import { Play, TrendingUp, Clock, AlertTriangle, Sparkles, DollarSign, BrainCircuit } from 'lucide-react';
import { cn } from '@eaimos/shared';

interface AnalyticsCardsProps {
  metrics: {
    totalRuns: number;
    successRate: number;
    avgLatency: number;
    totalCost: number;
    totalTokens: number;
  };
  className?: string;
}

export function AnalyticsCards({ metrics, className }: AnalyticsCardsProps) {
  const cards = [
    { label: 'Total Executions', value: metrics.totalRuns.toLocaleString(), icon: Play, color: 'text-violet-400', bg: 'bg-violet-600/10' },
    { label: 'Avg Success Rate', value: `${metrics.successRate.toFixed(1)}%`, icon: Sparkles, color: 'text-emerald-400', bg: 'bg-emerald-600/10' },
    { label: 'Avg Latency', value: `${(metrics.avgLatency / 1000).toFixed(2)}s`, icon: Clock, color: 'text-cyan-400', bg: 'bg-cyan-600/10' },
    { label: 'Cumulative Costs', value: `$${metrics.totalCost.toFixed(4)}`, icon: DollarSign, color: 'text-amber-400', bg: 'bg-amber-600/10' },
  ];

  return (
    <div className={cn('grid grid-cols-2 lg:grid-cols-4 gap-4', className)}>
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div key={c.label} className="p-5 rounded-xl border border-white/5 bg-neutral-950/40 hover:border-white/10 transition-all flex items-center justify-between text-left group">
            <div>
              <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">{c.label}</span>
              <span className="text-xl font-extrabold text-white mt-2 block">{c.value}</span>
            </div>
            <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform', c.bg, c.color)}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface ChartData {
  name: string;
  runs: number;
  cost: number;
  latency: number;
}

interface AnalyticsChartsProps {
  data: ChartData[];
  className?: string;
}

export function AnalyticsCharts({ data, className }: AnalyticsChartsProps) {
  return (
    <div className={cn('grid grid-cols-1 lg:grid-cols-3 gap-6', className)}>
      {/* Runs Chart */}
      <div className="p-5 rounded-xl border border-white/5 bg-neutral-950/40 text-left flex flex-col justify-between h-[300px]">
        <div className="mb-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Runs Timeline</span>
          <span className="text-xs text-neutral-400">Total executions over time</span>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="runsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis dataKey="name" stroke="#525252" fontSize={9} />
              <YAxis stroke="#525252" fontSize={9} />
              <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#262626', fontSize: 10 }} />
              <Area type="monotone" dataKey="runs" stroke="#8b5cf6" fillOpacity={1} fill="url(#runsGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Costs Chart */}
      <div className="p-5 rounded-xl border border-white/5 bg-neutral-950/40 text-left flex flex-col justify-between h-[300px]">
        <div className="mb-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Cost Trends</span>
          <span className="text-xs text-neutral-400">Model cost allocation metrics</span>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis dataKey="name" stroke="#525252" fontSize={9} />
              <YAxis stroke="#525252" fontSize={9} />
              <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#262626', fontSize: 10 }} />
              <Line type="monotone" dataKey="cost" stroke="#f59e0b" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Latency Chart */}
      <div className="p-5 rounded-xl border border-white/5 bg-neutral-950/40 text-left flex flex-col justify-between h-[300px]">
        <div className="mb-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Latency Performance</span>
          <span className="text-xs text-neutral-400">Average response latency profiles</span>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis dataKey="name" stroke="#525252" fontSize={9} />
              <YAxis stroke="#525252" fontSize={9} />
              <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#262626', fontSize: 10 }} />
              <Bar dataKey="latency" fill="#06b6d4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
