'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAgentDetails, useAgents, useAgentRuns, useRunLogs } from '@/features/agents/hooks';
import { useModels } from '@/features/ai-platform/hooks';
import { AgentDefinition, AgentType } from '@/features/agents/types';
import { AgentAvatar } from '@/features/agents/components/badges';
import { KnowledgeSelector, ToolSelector, MemorySelector } from '@/features/agents/components/selectors';
import { RunTimeline, ExecutionLog } from '@/features/agents/components/timeline';
import { AnalyticsCharts, AnalyticsCards } from '@/features/agents/components/analytics';
import { Button } from '@/components/ui/button';
import { 
  Bot, Settings, Sparkles, Folder, Play, CheckCircle2, ChevronRight, 
  ArrowLeft, Cpu, ShieldCheck, Database, HelpCircle, Activity 
} from 'lucide-react';
import { cn } from '@eaimos/shared';
import { CodeBlock } from '@/components/ui/code-block';

interface RouteProps {
  params: Promise<{ id: string }>;
}

export default function AgentDetailsRoute({ params }: RouteProps) {
  const router = useRouter();
  const { id } = React.use(params);
  
  const { agent, isLoading, isError } = useAgentDetails(id);
  const { updateAgent } = useAgents();
  const { models } = useModels();

  const [activeTab, setActiveTab] = React.useState<string>('overview');

  // Local state for configuration updates
  const [name, setName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [agentType, setAgentType] = React.useState<AgentType>('CUSTOM');
  const [preferredModel, setPreferredModel] = React.useState('');
  const [temperature, setTemperature] = React.useState(0.7);
  const [systemPrompt, setSystemPrompt] = React.useState('');
  const [selectedCollections, setSelectedCollections] = React.useState<string[]>([]);
  const [memoryEnabled, setMemoryEnabled] = React.useState(true);
  const [maxMemoryItems, setMaxMemoryItems] = React.useState(20);
  const [allowedTools, setAllowedTools] = React.useState<string[]>([]);

  // Sync state with loaded agent details
  React.useEffect(() => {
    if (agent) {
      setName(agent.name);
      setDescription(agent.description || '');
      setAgentType(agent.agent_type);
      setPreferredModel(agent.preferred_model || '');
      setTemperature(agent.temperature);
      setSystemPrompt(agent.system_prompt || '');
      setMemoryEnabled(agent.memory_enabled);
      setMaxMemoryItems(agent.max_memory_items);
      setAllowedTools(agent.allowed_tools || []);
    }
  }, [agent]);

  const handleSave = () => {
    updateAgent.mutate(
      {
        id,
        data: {
          name,
          description: description || null,
          agent_type: agentType,
          preferred_model: preferredModel || null,
          temperature,
          system_prompt: systemPrompt || null,
          memory_enabled: memoryEnabled,
          max_memory_items: maxMemoryItems,
          allowed_tools: allowedTools,
        },
      },
      {
        onSuccess: () => {
          alert('Configuration updated successfully!');
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center text-neutral-500 flex flex-col items-center gap-3">
        <span className="animate-pulse">Loading agent details...</span>
      </div>
    );
  }

  if (isError || !agent) {
    return (
      <div className="py-20 text-center text-neutral-500 flex flex-col items-center gap-3">
        <HelpCircle className="w-8 h-8 opacity-25" />
        <span>Agent definition not found or permission error.</span>
        <Button variant="outline" onClick={() => router.push('/dashboard/agents')} className="mt-4">
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'config', label: 'Configuration' },
    { id: 'prompt', label: 'System Instructions' },
    { id: 'versioning', label: 'Versioning & Diffs' },
    { id: 'memory-viz', label: 'Memory Visualizer' },
    { id: 'tool-execution', label: 'Tool Inspector' },
    { id: 'collaboration', label: 'Multi-Agent Flow' },
    { id: 'evaluations', label: 'Evaluations' },
    { id: 'knowledge', label: 'Knowledge (RAG)' },
    { id: 'memory', label: 'Memory' },
    { id: 'tools', label: 'Tools' },
    { id: 'runs', label: 'Runs' },
    { id: 'logs', label: 'Logs' },
    { id: 'analytics', label: 'Analytics' },
  ] as const;

  // Visual version diff state helper
  const oldPromptVersion = "You are a basic marketing assistant helper.";
  const [commentInput, setCommentInput] = React.useState('');
  const [comments, setComments] = React.useState([
    { author: 'john@viptant.com', date: '2 days ago', text: 'Tuned SPF instructions parameters.' },
    { author: 'system@viptant.com', date: '4 days ago', text: 'Initial agent draft definition registered.' }
  ]);

  const handleRollback = () => {
    setSystemPrompt(oldPromptVersion);
    alert('System prompt rolled back to v1 baseline.');
  };

  const handleAddComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentInput.trim()) return;
    setComments([{ author: 'you@viptant.com', date: 'Just now', text: commentInput }, ...comments]);
    setCommentInput('');
  };

  return (
    <div className="space-y-6 text-left max-w-6xl mx-auto">
      {/* Header Profile card */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-5">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/dashboard/agents')}
            className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-neutral-400 hover:text-white transition-all cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <AgentAvatar name={agent.name} avatarColor={agent.avatar_color} size="lg" />
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white">{agent.name}</h2>
            <p className="text-xs text-neutral-400 mt-1 uppercase font-mono tracking-wider">{agent.agent_type} · ID: {agent.id.slice(0, 8)}</p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/dashboard/agents/playground?agentId=${agent.id}`)}
            className="h-10 text-xs font-semibold gap-1.5 border-white/5 text-neutral-300 hover:text-white cursor-pointer"
          >
            <Play className="w-4 h-4 text-violet-400" /> Playground
          </Button>
          <Button
            variant="violet"
            onClick={handleSave}
            className="h-10 text-xs font-semibold gap-1.5"
            isLoading={updateAgent.isPending}
          >
            <CheckCircle2 className="w-4 h-4" /> Save Changes
          </Button>
        </div>
      </div>

      {/* Tabs navigation list */}
      <div className="flex gap-1 overflow-x-auto justify-start border-b border-white/5 scrollbar-none pb-0.5">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={cn(
              'px-4 py-2 text-xs font-semibold transition-colors cursor-pointer border-b-2 -mb-0.5 whitespace-nowrap',
              activeTab === t.id
                ? 'border-violet-500 text-violet-400'
                : 'border-transparent text-neutral-500 hover:text-neutral-300'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="p-6 rounded-2xl border border-white/10 bg-neutral-950/40 glass">
        
        {/* OVERVIEW PANEL */}
        {activeTab === 'overview' && (
          <div className="space-y-8 animate-fadeIn">
            {/* KPI statistics cards */}
            <AnalyticsCards 
              metrics={{
                totalRuns: 42,
                successRate: 97.6,
                avgLatency: 2800,
                totalCost: 0.1245,
                totalTokens: 12500
              }}
            />

            {/* General details split */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs font-mono border-t border-white/5 pt-6 leading-relaxed">
              <div className="space-y-3.5">
                <div className="flex justify-between"><span className="text-neutral-500">Agent Name:</span> <span className="text-white font-bold">{agent.name}</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Classification:</span> <span className="text-white uppercase">{agent.agent_type}</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Model Preferences:</span> <span className="text-white">{agent.preferred_model || 'Gateway default'}</span></div>
              </div>

              <div className="space-y-3.5">
                <div className="flex justify-between"><span className="text-neutral-500">Allowed Tools:</span> <span className="text-white">{agent.allowed_tools.length > 0 ? agent.allowed_tools.join(', ') : 'None'}</span></div>
                <div className="flex justify-between"><span className="text-neutral-500">Memory Config:</span> <span className="text-white">{agent.memory_enabled ? `Active (${agent.max_memory_items} turns)` : 'Disabled'}</span></div>
              </div>
            </div>
          </div>
        )}

        {/* CONFIGURATION PANEL */}
        {activeTab === 'config' && (
          <div className="space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Agent Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Agent Classification *</label>
                <select
                  value={agentType}
                  onChange={(e) => setAgentType(e.target.value as AgentType)}
                  className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 transition-colors"
                >
                  <option value="CRM">CRM & Operations</option>
                  <option value="CONTENT">Content Studio</option>
                  <option value="MARKETING">Marketing & Creative</option>
                  <option value="CAMPAIGN">Campaign Orchestration</option>
                  <option value="RESEARCH">Semantic Research</option>
                  <option value="CUSTOM">Custom Builder</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Preferred LLM Model *</label>
                <select
                  value={preferredModel}
                  onChange={(e) => setPreferredModel(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 transition-colors font-mono"
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.name || m.id}>{m.name || m.id}</option>
                  ))}
                  {models.length === 0 && <option value="">No models available (Gateway default)</option>}
                </select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center text-[10px] font-bold text-neutral-400 uppercase tracking-wider">
                  <span>Model Temperature</span>
                  <span className="text-violet-400 font-mono">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-violet-600 mt-2.5"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Description & Instructions Summary</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors leading-relaxed"
              />
            </div>
          </div>
        )}

        {/* SYSTEM PROMPT PANEL */}
        {activeTab === 'prompt' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">System Instructions Prompt</label>
              <span className="text-[9px] text-neutral-500 block mt-0.5">Define core rules, boundaries, and personality voice vectors.</span>
            </div>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={10}
              className="w-full px-4 py-3 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 transition-colors font-mono leading-relaxed"
            />
          </div>
        )}

        {/* VERSION HISTORY DIFF PANEL */}
        {activeTab === 'versioning' && (
          <div className="space-y-6 animate-fadeIn text-left">
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <div>
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Version Comparison Diff</label>
                <span className="text-[9px] text-neutral-500 block mt-0.5">Audit prompts variations and rollback to baseline blueprints.</span>
              </div>
              <Button variant="outline" size="sm" onClick={handleRollback} className="h-8 text-[11px] border-white/5 text-neutral-300 hover:text-white">
                Rollback to v1
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-red-950/15 border border-red-500/10 font-mono text-[10.5px]">
                <span className="text-red-400 block font-bold mb-2">v1 - Historical Prompt</span>
                <p className="text-red-300/80 leading-relaxed strike">{oldPromptVersion}</p>
              </div>

              <div className="p-4 rounded-lg bg-emerald-950/15 border border-emerald-500/10 font-mono text-[10.5px]">
                <span className="text-emerald-400 block font-bold mb-2">v2 - Current Prompt (Draft)</span>
                <p className="text-emerald-300/90 leading-relaxed">{systemPrompt || 'No prompt set.'}</p>
              </div>
            </div>

            {/* Version comments log */}
            <div className="space-y-4 border-t border-white/5 pt-5">
              <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Comments Log</span>
              
              <form onSubmit={handleAddComment} className="flex gap-2">
                <input
                  type="text"
                  value={commentInput}
                  onChange={(e) => setCommentInput(e.target.value)}
                  placeholder="Add version adjustment comment..."
                  className="flex-1 px-3 py-1.5 rounded bg-neutral-900 border border-white/5 text-xs text-white focus:outline-none"
                />
                <Button type="submit" variant="violet" className="h-8 text-[11px] px-4 font-semibold">Post</Button>
              </form>

              <div className="space-y-3 font-mono text-[10px]">
                {comments.map((c, i) => (
                  <div key={i} className="p-2.5 rounded bg-neutral-900/40 border border-white/2">
                    <div className="flex justify-between text-[9px] text-neutral-500 mb-1">
                      <span>{c.author}</span>
                      <span>{c.date}</span>
                    </div>
                    <p className="text-neutral-300">{c.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* MEMORY VISUALIZER PANEL */}
        {activeTab === 'memory-viz' && (
          <div className="space-y-6 animate-fadeIn text-left">
            <div>
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Dynamic Memory Visualization</label>
              <span className="text-[9px] text-neutral-500 block mt-0.5">Monitor context namespaces and long term DB storage.</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-b border-white/5 pb-6">
              {/* Gauges */}
              <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 space-y-4">
                <span className="text-[9px] font-bold text-neutral-500 font-mono block">Memory Allocation Gauge</span>
                <div className="flex justify-between items-center text-xs font-mono">
                  <span>Conversation Memory:</span> <span className="text-violet-400 font-bold">12 / 20 turns</span>
                </div>
                <div className="w-full bg-neutral-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-violet-500 h-full w-[60%]" />
                </div>
                <div className="flex justify-between items-center text-xs font-mono mt-2">
                  <span>Knowledge Context Size:</span> <span className="text-cyan-400 font-bold">4.2KB / 120KB</span>
                </div>
                <div className="w-full bg-neutral-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-cyan-500 h-full w-[5%]" />
                </div>
              </div>

              {/* Namespaces timeline */}
              <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 space-y-4">
                <span className="text-[9px] font-bold text-neutral-500 font-mono block">Storage Buckets Status</span>
                <div className="grid grid-cols-2 gap-3 text-[10px] font-mono">
                  <div className="p-2 rounded bg-neutral-900 border border-white/5 text-neutral-400">
                    <span className="text-violet-300 block font-bold">Brand memory</span>
                    "Maintain strict corporate SPF audits tone."
                  </div>
                  <div className="p-2 rounded bg-neutral-900 border border-white/5 text-neutral-400">
                    <span className="text-cyan-300 block font-bold">Org memory</span>
                    "Workspace org ID: Acme Corp verified."
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TOOL EXECUTION INSPECTOR PANEL */}
        {activeTab === 'tool-execution' && (
          <div className="space-y-6 animate-fadeIn text-left font-mono text-[10.5px]">
            <div>
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Tool Calls Executions Logs</label>
              <span className="text-[9px] text-neutral-500 block mt-0.5">Audit JSON structures and latency payloads of tool dispatches.</span>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/60 space-y-3.5">
                <div className="flex justify-between items-center border-b border-white/2 pb-2">
                  <span className="text-violet-400 font-bold font-mono">Call Tool: webhooks</span>
                  <span className="text-emerald-400 font-bold">SUCCESS · 420ms</span>
                </div>
                <div>
                  <span className="text-neutral-500 block text-[9px] uppercase font-bold mb-1">Request Payload</span>
                  <CodeBlock code={JSON.stringify({ target: "SPF", domain: "viptant.com" }, null, 2)} />
                </div>
                <div>
                  <span className="text-neutral-500 block text-[9px] uppercase font-bold mb-1">Response Payload</span>
                  <CodeBlock code={JSON.stringify({ spf_record: "v=spf1 include:_spf.google.com ~all", healthy: true }, null, 2)} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MULTI AGENT COLLABORATION PANEL */}
        {activeTab === 'collaboration' && (
          <div className="space-y-6 animate-fadeIn text-left">
            <div>
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Multi-Agent Collaboration Pipe</label>
              <span className="text-[9px] text-neutral-500 block mt-0.5">Visual map tracing pipeline execution steps between agent profiles.</span>
            </div>

            {/* Framer motion steppers pipeline */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between p-6 bg-neutral-950/40 rounded-xl border border-white/5 select-none relative overflow-x-auto min-w-[500px]">
              {[
                { name: 'Marketing Agent', type: 'Trigger' },
                { name: 'Research Agent', type: 'Enrichment' },
                { name: 'SEO Agent', type: 'Keywords' },
                { name: 'Content Agent', type: 'Writer' },
                { name: 'Campaign Agent', type: 'Publisher' },
              ].map((ag, idx) => (
                <React.Fragment key={ag.name}>
                  <div className="p-3.5 rounded-xl border border-white/8 bg-neutral-900 flex flex-col items-center justify-center shrink-0 w-32 shadow-md">
                    <Bot className="w-5 h-5 text-violet-400 mb-1.5" />
                    <span className="text-[10px] font-bold text-white text-center block truncate max-w-full leading-tight">{ag.name}</span>
                    <span className="text-[8px] font-mono text-neutral-500 uppercase mt-1 block">{ag.type}</span>
                  </div>
                  {idx < 4 && (
                    <div className="flex-1 flex justify-center items-center font-mono text-[9px] text-violet-500">
                      ➜
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {/* EVALUATIONS PANEL */}
        {activeTab === 'evaluations' && (
          <div className="space-y-8 animate-fadeIn text-left font-mono">
            {/* KPI grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 text-left">
                <span className="text-[9px] font-bold text-neutral-500 uppercase tracking-wider block">Quality Score</span>
                <span className="text-lg font-bold text-emerald-400 mt-2 block">96.8%</span>
              </div>
              <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 text-left">
                <span className="text-[9px] font-bold text-neutral-500 uppercase tracking-wider block">Hallucination Index</span>
                <span className="text-lg font-bold text-violet-400 mt-2 block">1.2%</span>
              </div>
              <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 text-left">
                <span className="text-[9px] font-bold text-neutral-500 uppercase tracking-wider block">Tool Efficiency</span>
                <span className="text-lg font-bold text-cyan-400 mt-2 block">98.5%</span>
              </div>
              <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 text-left">
                <span className="text-[9px] font-bold text-neutral-500 uppercase tracking-wider block">Knowledge Citation</span>
                <span className="text-lg font-bold text-amber-400 mt-2 block">100%</span>
              </div>
            </div>

            {/* Prompt efficiency advice */}
            <div className="p-4 rounded-xl border border-white/5 bg-neutral-950/40">
              <span className="text-[10px] font-bold text-neutral-400 block mb-2">Prompt Optimization Feedback</span>
              <p className="text-neutral-400 text-xs leading-relaxed">
                System instructions prompts show high alignment metrics. Recommended: increase temperature to 0.8 to introduce slightly richer sentence structures inside copy outputs if required.
              </p>
            </div>
          </div>
        )}

        {/* KNOWLEDGE (RAG) PANEL */}
        {activeTab === 'knowledge' && (
          <div className="animate-fadeIn">
            <KnowledgeSelector
              selectedCollections={selectedCollections}
              onChangeCollections={setSelectedCollections}
            />
          </div>
        )}

        {/* MEMORY PANEL */}
        {activeTab === 'memory' && (
          <div className="animate-fadeIn">
            <MemorySelector
              memoryEnabled={memoryEnabled}
              onChangeMemoryEnabled={setMemoryEnabled}
              maxMemoryItems={maxMemoryItems}
              onChangeMaxMemoryItems={setMaxMemoryItems}
            />
          </div>
        )}

        {/* TOOLS PANEL */}
        {activeTab === 'tools' && (
          <div className="animate-fadeIn">
            <ToolSelector
              allowedTools={allowedTools}
              onChange={setAllowedTools}
            />
          </div>
        )}

        {/* RUNS PANEL */}
        {activeTab === 'runs' && (
          <div className="space-y-4 text-left animate-fadeIn">
            <div>
              <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Recent Executions</span>
              <span className="text-[9px] text-neutral-600 mt-0.5 block">Audit historical inputs, latencies, and tool calls outcomes.</span>
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
        )}

        {/* LOGS PANEL */}
        {activeTab === 'logs' && (
          <div className="animate-fadeIn">
            <ExecutionLog 
              logs={[
                { id: '1', run_id: '1', organization_id: '1', level: 'INFO', step_type: 'initialize', content: 'Agent definition kopier initialized.', meta_data: {} },
                { id: '2', run_id: '1', organization_id: '1', level: 'INFO', step_type: 'tool_call', content: 'Executing webhook verify call on Viptant domain DNS target record.', meta_data: {} },
                { id: '3', run_id: '1', organization_id: '1', level: 'INFO', step_type: 'parse', content: 'TXT target records parsed successfully. SPF resolved.', meta_data: {} }
              ]} 
            />
          </div>
        )}

        {/* ANALYTICS PANEL */}
        {activeTab === 'analytics' && (
          <div className="animate-fadeIn">
            <AnalyticsCharts 
              data={[
                { name: 'Mon', runs: 12, cost: 0.024, latency: 1400 },
                { name: 'Tue', runs: 18, cost: 0.038, latency: 2200 },
                { name: 'Wed', runs: 24, cost: 0.045, latency: 1800 },
                { name: 'Thu', runs: 15, cost: 0.029, latency: 1900 },
                { name: 'Fri', runs: 30, cost: 0.052, latency: 2400 },
              ]}
            />
          </div>
        )}

      </div>
    </div>
  );
}
