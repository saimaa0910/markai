'use client';
import * as React from 'react';
import { useRouter } from 'next/navigation';
import { usePrompts, usePromptAnalytics, usePromptTemplates } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  BookOpen, Plus, Sparkles, TrendingUp, Cpu, 
  Clock, DollarSign, Activity, Settings2, BarChart2, Library, SlidersHorizontal 
} from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend 
} from 'recharts';

export function DashboardPage() {
  const router = useRouter();
  const { prompts, isLoading } = usePrompts();
  const { stats } = usePromptAnalytics();
  const { templates } = usePromptTemplates();

  // Dynamic metrics telemetry data from backend stats
  const chartsData = React.useMemo(() => {
    if (stats.dailyExecutions && stats.dailyExecutions.length > 0) {
      return stats.dailyExecutions;
    }
    return [
      { date: 'Today', executions: stats.totalExecutions || 0, latency: stats.avgLatencyMs || 0 }
    ];
  }, [stats]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Page Header */}
      <PageHeader
        title="Prompt Registry Dashboard"
        description="Unified management console and analytics portal for prompt templates, version flows, and sandbox runs."
        icon={<BookOpen className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Prompt Engineering</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <a href="/dashboard/prompts/testing">
              <Button variant="outline" size="sm" className="h-8 text-[11px] border-white/5 bg-neutral-900" onClick={(e) => {
      e.preventDefault();
      router.push('/dashboard/prompts/testing');
    }}>
                <SlidersHorizontal className="w-3.5 h-3.5 mr-1" />
                Testing Lab
              </Button>
            </a>
            <a href="/dashboard/prompts/editor">
              <Button variant="violet" size="sm" className="h-8 text-[11px]" onClick={(e) => {
      e.preventDefault();
      router.push('/dashboard/prompts/editor');
    }}>
                <Plus className="w-3.5 h-3.5 mr-1" />
                Create Prompt
              </Button>
            </a>
          </div>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
        <StatCard
          title="Total Prompts"
          value={stats.totalPrompts}
          icon={<Library className="w-4 h-4 text-violet-400" />}
          description="Registered prompt families"
          isLoading={isLoading}
        />
        <StatCard
          title="Average Latency"
          value={`${stats.avgLatencyMs}ms`}
          icon={<Clock className="w-4 h-4 text-sky-400" />}
          description="LLM response delays"
          isLoading={isLoading}
        />
        <StatCard
          title="Average Cost"
          value={`$${stats.avgCostUsd.toFixed(5)}`}
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          description="Expenditure per execution"
          isLoading={isLoading}
        />
        <StatCard
          title="Success Rate"
          value={`${stats.successRate}%`}
          icon={<Activity className="w-4 h-4 text-amber-400" />}
          description="Zero-failure model checks"
          isLoading={isLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CHART WIDGETS (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          
          {/* Prompt Executions AreaChart */}
          <Card className="flex flex-col gap-4">
            <div>
              <h4 className="font-bold text-white text-sm">Registry Executions Volume</h4>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Daily transaction hits logged across connected AI Agents.</p>
            </div>

            <div className="h-[210px] w-full mt-2 text-xs">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="execGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                  <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                  <Tooltip />
                  <Area type="monotone" dataKey="executions" stroke="#8b5cf6" strokeWidth={2} fill="url(#execGrad)" name="Executions" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Prompt latency BarChart */}
          <Card className="flex flex-col gap-4">
            <div>
              <h4 className="font-bold text-white text-sm">Response Latency Profile</h4>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Average prompt response latency logged daily.</p>
            </div>

            <div className="h-[210px] w-full mt-2 text-xs">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                  <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                  <Tooltip />
                  <Bar dataKey="latency" fill="#10b981" radius={4} name="Latency (ms)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

        </div>

        {/* DETAILS LISTINGS (Right 1 column) */}
        <div className="flex flex-col gap-6">
          
          {/* Preset templates list */}
          <Card className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-white text-sm">Prebuilt Templates Gallery</h4>
                <p className="text-[11px] text-neutral-500 mt-0.5">Quick starting copy templates</p>
              </div>
              <a href="/dashboard/prompts/templates" className="text-[10px] text-violet-400 font-semibold hover:underline">
                View All
              </a>
            </div>

            <div className="flex flex-col gap-3 mt-1">
              {templates.slice(0, 3).map((item: any) => (
                <div 
                  key={item.name} 
                  className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/20 flex flex-col gap-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-white truncate">{item.name}</span>
                    <Badge variant="violet" className="text-[9px] uppercase font-bold shrink-0">{item.category}</Badge>
                  </div>
                  <p className="text-[10px] text-neutral-400 line-clamp-2 leading-relaxed font-mono">
                    {item.content}
                  </p>
                </div>
              ))}
            </div>
          </Card>

          {/* Category Distribution list */}
          <Card className="flex flex-col gap-4">
            <div>
              <h4 className="font-bold text-white text-sm">Registry Distribution</h4>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Categorized listing summary breakdowns.</p>
            </div>

            <div className="flex flex-col gap-3 mt-1">
              {stats.categoriesBreakdown.length > 0 ? (
                stats.categoriesBreakdown.map((cat: any) => (
                  <div key={cat.name} className="flex justify-between items-center text-xs font-mono">
                    <span className="text-neutral-400">{cat.name}</span>
                    <Badge variant="neutral">{cat.value} prompts</Badge>
                  </div>
                ))
              ) : (
                <span className="text-[10px] text-neutral-600 text-center py-4">No categories indexed.</span>
              )}
            </div>
          </Card>

        </div>
      </div>
    </div>
  );
}
