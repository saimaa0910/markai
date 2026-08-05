'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  BarChart2, TrendingUp, DollarSign, Users, Sparkles, Filter, Calendar, ArrowUpRight, ArrowDownRight, Activity, Cpu, Layers,
} from 'lucide-react';
import { useAnalyticsOverview } from '../queries';

export default function AnalyticsPage() {
  const { data: analytics, isLoading } = useAnalyticsOverview();

  const mockOverview = React.useMemo(() => {
    if (analytics) return analytics;
    return {
      total_revenue: 128450,
      active_leads: 420,
      conversion_rate: 18.4,
      total_ai_tokens: 3450000,
      total_agent_runs: 1240,
      funnel_steps: [
        { step_name: 'Visitor Impressions', count: 45000, conversion_percent: 100 },
        { step_name: 'Lead Qualification', count: 8200, conversion_percent: 18.2 },
        { step_name: 'Proposal Sent', count: 2100, conversion_percent: 25.6 },
        { step_name: 'Closed Won', count: 828, conversion_percent: 39.4 },
      ],
    };
  }, [analytics]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart2 className="w-6 h-6 text-emerald-400" /> Executive Analytics & Funnel Platform
          </h1>
          <p className="text-sm text-zinc-500 mt-1">Cross-platform revenue attribution, funnel conversion, and AI performance metrics</p>
        </div>
        <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 p-1.5 rounded-lg text-xs text-zinc-400 font-medium">
          <Calendar className="w-4 h-4 text-emerald-400" /> Last 30 Days
        </div>
      </div>

      {/* Top Metric Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Total Revenue</p>
            <p className="text-2xl font-bold text-white mt-1">${mockOverview.total_revenue.toLocaleString()}</p>
            <span className="text-[11px] text-emerald-400 flex items-center gap-0.5 mt-1 font-semibold"><ArrowUpRight className="w-3.5 h-3.5" /> +14.2% MoM</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center"><DollarSign className="w-5 h-5" /></div>
        </div>

        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Active Leads</p>
            <p className="text-2xl font-bold text-white mt-1">{mockOverview.active_leads}</p>
            <span className="text-[11px] text-emerald-400 flex items-center gap-0.5 mt-1 font-semibold"><ArrowUpRight className="w-3.5 h-3.5" /> +8.7% MoM</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center"><Users className="w-5 h-5" /></div>
        </div>

        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Conversion Rate</p>
            <p className="text-2xl font-bold text-white mt-1">{mockOverview.conversion_rate}%</p>
            <span className="text-[11px] text-emerald-400 flex items-center gap-0.5 mt-1 font-semibold"><ArrowUpRight className="w-3.5 h-3.5" /> +2.1% MoM</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center"><TrendingUp className="w-5 h-5" /></div>
        </div>

        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Agent Executions</p>
            <p className="text-2xl font-bold text-white mt-1">{mockOverview.total_agent_runs}</p>
            <span className="text-[11px] text-violet-400 flex items-center gap-0.5 mt-1 font-semibold"><Cpu className="w-3.5 h-3.5" /> 99.8% Success</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-violet-500/20 text-violet-400 flex items-center justify-center"><Sparkles className="w-5 h-5" /></div>
        </div>
      </div>

      {/* Funnel & Performance Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Conversion Funnel */}
        <div className="lg:col-span-7 bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" /> Sales & Marketing Conversion Funnel
          </h2>
          <div className="space-y-4 pt-2">
            {mockOverview.funnel_steps.map((step, i) => (
              <div key={i} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-zinc-300">
                  <span className="font-medium">{step.step_name}</span>
                  <span className="font-bold text-white">{step.count.toLocaleString()} ({step.conversion_percent}%)</span>
                </div>
                <div className="w-full h-3 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${step.conversion_percent}%` }}
                    transition={{ duration: 0.8, delay: i * 0.1 }}
                    className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Gateway Efficiency */}
        <div className="lg:col-span-5 bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-4 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-violet-400" /> AI System Efficiency
            </h2>
            <div className="mt-6 space-y-4">
              <div className="flex items-center justify-between p-3.5 bg-zinc-950/40 rounded-xl border border-zinc-800">
                <span className="text-xs text-zinc-400">Total Tokens Processed</span>
                <span className="text-sm font-bold text-white">{(mockOverview.total_ai_tokens / 1000000).toFixed(2)}M Tokens</span>
              </div>
              <div className="flex items-center justify-between p-3.5 bg-zinc-950/40 rounded-xl border border-zinc-800">
                <span className="text-xs text-zinc-400">Avg Gateway Latency</span>
                <span className="text-sm font-bold text-emerald-400">142ms</span>
              </div>
              <div className="flex items-center justify-between p-3.5 bg-zinc-950/40 rounded-xl border border-zinc-800">
                <span className="text-xs text-zinc-400">Model Cache Hit Ratio</span>
                <span className="text-sm font-bold text-violet-400">84.2%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
