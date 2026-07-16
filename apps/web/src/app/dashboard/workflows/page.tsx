'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useWorkflows } from '@/features/workflows/hooks';
import { WorkflowDefinition, WorkflowTrigger } from '@/features/workflows/types';
import { Button } from '@/components/ui/button';
import { AnalyticsCharts, AnalyticsCards } from '@/features/agents/components/analytics';
import { 
  Activity, Play, Plus, Search, HelpCircle, 
  Trash2, RefreshCw, Copy, Sliders, ToggleLeft, ArrowRight 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

export default function WorkflowsDashboardPage() {
  const router = useRouter();
  const { workflows, isLoading, createWorkflow, deleteWorkflow } = useWorkflows(1, 100);

  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedTrigger, setSelectedTrigger] = React.useState<string>('ALL');

  const filtered = workflows.filter((w) => {
    const matchesSearch = w.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (w.description || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTrigger = selectedTrigger === 'ALL' || w.trigger === selectedTrigger;
    return matchesSearch && matchesTrigger;
  });

  const handleDuplicate = (wf: WorkflowDefinition) => {
    createWorkflow.mutate({
      name: `${wf.name} (Copy)`,
      description: wf.description,
      status: 'DRAFT',
      trigger: wf.trigger,
      steps_definition: wf.steps_definition,
      cron_expression: wf.cron_expression,
      webhook_config: wf.webhook_config,
      max_retries: wf.max_retries,
      timeout_seconds: wf.timeout_seconds,
    });
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this workflow blueprint?')) {
      deleteWorkflow.mutate(id);
    }
  };

  // Mock aggregated analytics stats matching n8n/make look
  const metrics = {
    totalRuns: 1240,
    successRate: 99.1,
    avgLatency: 1850,
    totalCost: 0.842,
    totalTokens: 64200
  };

  const chartData = [
    { name: 'Mon', runs: 120, cost: 0.08, latency: 1400 },
    { name: 'Tue', runs: 180, cost: 0.12, latency: 2200 },
    { name: 'Wed', runs: 240, cost: 0.16, latency: 1600 },
    { name: 'Thu', runs: 190, cost: 0.13, latency: 1900 },
    { name: 'Fri', runs: 310, cost: 0.22, latency: 2400 },
  ];

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-violet-400" /> Workflows Orchestrator
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            Design multi-agent automation loops, schedule content pipelines, and configure webhooks.
          </p>
        </div>

        <Button
          variant="violet"
          onClick={() => router.push('/dashboard/workflows/create')}
          className="h-10 text-xs font-semibold gap-1.5"
        >
          <Plus className="w-4 h-4" /> Create Workflow
        </Button>
      </div>

      {/* KPI stats */}
      <AnalyticsCards metrics={metrics} />

      {/* Split pane details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Filterable active workflows list (col-span-8) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="flex flex-col sm:flex-row gap-3 justify-between items-center bg-neutral-950/40 p-3 rounded-xl border border-white/5">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Search className="w-4 h-4 text-neutral-500 shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search workflows name or description..."
                className="w-full sm:w-64 bg-transparent border-0 text-xs text-white placeholder-neutral-600 focus:outline-none"
              />
            </div>

            {/* Triggers categorization filter */}
            <div className="flex bg-neutral-900 rounded border border-white/5 p-0.5 shrink-0 select-none">
              {['ALL', 'MANUAL', 'SCHEDULED', 'WEBHOOK'].map((t) => (
                <button
                  key={t}
                  onClick={() => setSelectedTrigger(t)}
                  className={cn(
                    'px-2.5 py-1 rounded text-[9px] font-bold tracking-wide transition-colors cursor-pointer',
                    selectedTrigger === t ? 'bg-neutral-800 text-white' : 'text-neutral-500 hover:text-neutral-300'
                  )}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {isLoading ? (
            <div className="py-20 text-center text-neutral-500 flex flex-col items-center gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-violet-400" />
              <span className="text-xs">Fetching workflow blueprints...</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-20 text-center text-neutral-500 border border-dashed border-white/8 rounded-2xl bg-neutral-950/20 flex flex-col items-center justify-center p-6 gap-4">
              <Activity className="w-10 h-10 opacity-20" />
              <div>
                <h4 className="text-sm font-bold text-white">No Workflows Blueprints</h4>
                <p className="text-[11px] text-neutral-500 mt-1 max-w-xs mx-auto leading-relaxed">
                  Design sequential trigger-action loops connecting AI models, slack notifications, and webhook data mappings.
                </p>
              </div>
              <Button variant="violet" onClick={() => router.push('/dashboard/workflows/create')} className="h-8 text-[11px]">
                Create First Workflow
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {filtered.map((wf) => (
                <div 
                  key={wf.id}
                  className="group p-5 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/30 hover:bg-neutral-900/10 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-start mb-3 border-b border-white/5 pb-2.5">
                      <span className="text-[9px] font-bold font-mono uppercase tracking-wider text-violet-400 bg-violet-600/5 px-2 py-0.5 rounded border border-violet-500/10">
                        {wf.trigger}
                      </span>
                      <span className={cn(
                        'text-[8px] font-bold font-mono uppercase px-1.5 py-0.5 rounded border',
                        wf.status === 'ACTIVE' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-neutral-900 border-white/5 text-neutral-500'
                      )}>
                        {wf.status}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors truncate">
                      {wf.name}
                    </h4>
                    <p className="text-neutral-400 text-xs mt-1 min-h-[36px] line-clamp-2 leading-relaxed">
                      {wf.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="flex justify-between items-center border-t border-white/5 pt-4 mt-5">
                    <div className="flex gap-1">
                      <button 
                        onClick={() => handleDuplicate(wf)} 
                        className="p-1.5 rounded hover:bg-white/5 text-neutral-500 hover:text-white"
                        title="Duplicate Blueprint"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                      <button 
                        onClick={() => handleDelete(wf.id)} 
                        className="p-1.5 rounded hover:bg-white/5 text-neutral-500 hover:text-rose-400"
                        title="Delete Blueprint"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <Button
                      variant="violet"
                      size="sm"
                      onClick={() => router.push(`/dashboard/workflows/${wf.id}`)}
                      className="h-8 text-[11px] font-semibold gap-1 px-3"
                    >
                      Open Builder <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Analytics charts (col-span-4) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="border-b border-white/5 pb-2">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Performance charts</span>
            <span className="text-[9px] text-neutral-600 mt-0.5 block">Monitor execution latency and workload volumes.</span>
          </div>

          <AnalyticsCharts data={chartData} className="grid-cols-1 lg:grid-cols-1" />
        </div>
      </div>

    </div>
  );
}
