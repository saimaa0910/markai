'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAgents } from '@/features/agents/hooks';
import { AgentDefinition, AgentType } from '@/features/agents/types';
import { AgentCard } from '@/features/agents/components/agent-card';
import { RunTimeline } from '@/features/agents/components/timeline';
import { Button } from '@/components/ui/button';
import { 
  Bot, Plus, Search, Filter, RefreshCw, 
  Grid, List, Activity, ShieldAlert, Sparkles, DollarSign 
} from 'lucide-react';
import { cn } from '@eaimos/shared';
export default function AgentsDashboardPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = React.useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedType, setSelectedType] = React.useState<string>('ALL');

  const { 
    agents, 
    isLoading, 
    deleteAgent, 
    createAgent 
  } = useAgents(1, 100);

  // Filter agents locally
  const filteredAgents = agents.filter((a) => {
    const matchesSearch = a.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (a.description || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'ALL' || a.agent_type === selectedType;
    return matchesSearch && matchesType;
  });

  const handleDuplicate = (agent: AgentDefinition) => {
    createAgent.mutate({
      name: `${agent.name} (Copy)`,
      description: agent.description,
      agent_type: agent.agent_type,
      status: 'ACTIVE',
      system_prompt: agent.system_prompt,
      prompt_template_name: agent.prompt_template_name,
      allowed_tools: agent.allowed_tools,
      preferred_model: agent.preferred_model,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      memory_enabled: agent.memory_enabled,
      max_memory_items: agent.max_memory_items,
      max_iterations: agent.max_iterations,
      is_public: agent.is_public,
    });
  };

  const handleArchive = (agent: AgentDefinition) => {
    // Soft update status
    router.refresh();
  };

  const handleDelete = (agent: AgentDefinition) => {
    if (confirm(`Are you sure you want to delete ${agent.name}?`)) {
      deleteAgent.mutate(agent.id);
    }
  };

  // Mock static stats matching dashboard requirement
  const stats = [
    { label: 'Total Agents', value: agents.length, icon: Bot, color: 'text-violet-400', bg: 'bg-violet-600/10' },
    { label: 'Success Rate', value: '98.4%', icon: Sparkles, color: 'text-emerald-400', bg: 'bg-emerald-600/10' },
    { label: 'Avg Execution', value: '3.4s', icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-600/10' },
    { label: 'Total Cost Today', value: '$0.428', icon: DollarSign, color: 'text-amber-400', bg: 'bg-amber-600/10' },
  ];

  return (
    <div className="space-y-6 text-left">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Bot className="w-5 h-5 text-violet-400" /> AI Agent Studio
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            Build, deploy, and audit autonomous AI agents with localized memory.
          </p>
        </div>

        <Button
          variant="violet"
          onClick={() => router.push('/dashboard/agents/create')}
          className="h-10 text-xs font-semibold gap-1.5"
        >
          <Plus className="w-4 h-4" /> Create Agent
        </Button>
      </div>

      {/* Overview stats cards grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="p-4.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">{s.label}</span>
                <span className="text-lg font-extrabold text-white mt-1.5 block">{s.value}</span>
              </div>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${s.bg} ${s.color}`}>
                <Icon className="w-4.5 h-4.5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Main split work-desk */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Recent runs timeline feed (col-span-4) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="border-b border-white/5 pb-2">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Live Trace Feed</span>
            <span className="text-[9px] text-neutral-600 mt-0.5 block">Monitor streaming steps and tools dispatch logs.</span>
          </div>

          <RunTimeline 
            run={{
              id: '1',
              session_id: '1',
              organization_id: '1',
              user_input: 'Verify Viptant domain SPF records',
              agent_output: 'SPF configuration checked successfully.',
              plan: {},
              tool_calls: [{ name: 'webhooks', arguments: { target: 'SPF' } }],
              status: 'COMPLETED',
              error_message: null,
              iterations: 3,
              total_tokens: 420,
              latency_ms: 1250
            }}
          />
        </div>

        {/* Right Column: Active definitions list (col-span-8) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Filters controls bar */}
          <div className="flex flex-col sm:flex-row gap-3 justify-between items-center bg-neutral-950/40 p-3 rounded-xl border border-white/5">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Search className="w-4 h-4 text-neutral-500 shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search agent names, types or descriptions..."
                className="w-full sm:w-64 bg-transparent border-0 text-xs text-white placeholder-neutral-600 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
              {/* Category dropdown filters */}
              <div className="flex bg-neutral-900 rounded border border-white/5 p-0.5 shrink-0">
                {['ALL', 'MARKETING', 'CONTENT', 'CRM', 'CUSTOM'].map((t) => (
                  <button
                    key={t}
                    onClick={() => setSelectedType(t)}
                    className={`px-2 py-1 rounded text-[9px] font-bold tracking-wide transition-colors cursor-pointer ${
                      selectedType === t ? 'bg-neutral-800 text-white' : 'text-neutral-500 hover:text-neutral-300'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>

              {/* View Toggle */}
              <div className="flex bg-neutral-900 rounded border border-white/5 p-0.5 shrink-0">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-1 rounded cursor-pointer ${viewMode === 'grid' ? 'bg-neutral-800 text-white' : 'text-neutral-500'}`}
                >
                  <Grid className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1 rounded cursor-pointer ${viewMode === 'list' ? 'bg-neutral-800 text-white' : 'text-neutral-500'}`}
                >
                  <List className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Grid/List rendering */}
          {isLoading ? (
            <div className="py-20 text-center text-neutral-500 flex flex-col items-center gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-violet-400" />
              <span className="text-xs">Fetching active agent definitions...</span>
            </div>
          ) : filteredAgents.length === 0 ? (
            <div className="py-20 text-center text-neutral-500 border border-dashed border-white/8 rounded-2xl bg-neutral-950/20 flex flex-col items-center gap-4">
              <Bot className="w-10 h-10 opacity-20" />
              <div>
                <h4 className="text-sm font-bold text-white">No Agent Definitions Found</h4>
                <p className="text-[11px] text-neutral-500 mt-1 max-w-xs mx-auto leading-relaxed">
                  Start by launching a new agent mapping prompt templates, knowledge inputs, and allowed tool permissions.
                </p>
              </div>
              <Button
                variant="violet"
                onClick={() => router.push('/dashboard/agents/create')}
                className="h-8 text-[11px]"
              >
                Create First Agent
              </Button>
            </div>
          ) : (
            <div className={cn(
              viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 gap-6' : 'flex flex-col gap-3.5'
            )}>
              {filteredAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  viewMode={viewMode}
                  onDuplicate={handleDuplicate}
                  onArchive={handleArchive}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
