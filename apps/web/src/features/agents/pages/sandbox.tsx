'use client';

import * as React from 'react';
import { useSearchParams } from 'next/navigation';
import { useAgents, useAgentSessions, useAgentRuns, useAgentExecution, useRunLogs, useAgentDetails } from '@/features/agents/hooks';
import { AgentAvatar } from '@/features/agents/components/badges';
import { ExecutionLog } from '@/features/agents/components/timeline';
import { Button } from '@/components/ui/button';
import { 
  Send, Bot, MessageSquare, Terminal, Info, 
  Trash2, Database, BrainCircuit, Activity, Sparkles, DollarSign 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

interface Message {
  id: string;
  sender: 'user' | 'agent';
  content: string;
  timestamp: string;
  latency?: number;
  tokens?: number;
  cost?: number;
}

function AgentPlaygroundContent() {
  const searchParams = useSearchParams();
  const initialAgentId = searchParams.get('agentId') || '';

  const { agents } = useAgents(1, 100);
  const [selectedAgentId, setSelectedAgentId] = React.useState(initialAgentId);

  const { agent } = useAgentDetails(selectedAgentId || undefined);
  const { sessions, createSession } = useAgentSessions();

  const [activeSessionId, setActiveSessionId] = React.useState('');
  const { runs } = useAgentRuns(activeSessionId || undefined);
  const { runAgent } = useAgentExecution(activeSessionId || undefined);

  // Local state for chat message history and input query
  const [inputQuery, setInputQuery] = React.useState('');
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [latestRunId, setLatestRunId] = React.useState<string | undefined>(undefined);
  const { logs } = useRunLogs(latestRunId);

  // Auto-select first agent if none is selected
  React.useEffect(() => {
    if (initialAgentId) {
      setSelectedAgentId(initialAgentId);
    } else if (!selectedAgentId && agents.length > 0) {
      setSelectedAgentId(agents[0].id);
    }
  }, [initialAgentId, agents, selectedAgentId]);

  // Handle auto-session creation/lookup safely
  React.useEffect(() => {
    if (!selectedAgentId) return;

    const agentSession = sessions.find((s) => s.agent_id === selectedAgentId);
    if (agentSession) {
      if (activeSessionId !== agentSession.id) {
        setActiveSessionId(agentSession.id);
      }
    } else if (!createSession.isPending && !activeSessionId) {
      createSession.mutate(
        {
          agent_id: selectedAgentId,
          title: `Sandbox Session - ${new Date().toLocaleDateString()}`,
          context: {},
        },
        {
          onSuccess: (data) => {
            setActiveSessionId(data.id);
          },
        }
      );
    }
  }, [selectedAgentId, sessions, activeSessionId, createSession]);

  // Sync historical runs into messages safely
  React.useEffect(() => {
    if (runs.length > 0) {
      const msgs: Message[] = [];
      // Runs are returned latest first, reverse to display chronologically
      [...runs].reverse().forEach((r) => {
        msgs.push({
          id: `${r.id}-user`,
          sender: 'user',
          content: r.user_input,
          timestamp: new Date().toLocaleTimeString(),
        });
        if (r.agent_output) {
          msgs.push({
            id: `${r.id}-agent`,
            sender: 'agent',
            content: r.agent_output,
            timestamp: new Date().toLocaleTimeString(),
            latency: r.latency_ms || undefined,
            tokens: r.total_tokens,
            cost: (r.total_tokens * 0.000015), // estimate costs
          });
        }
      });
      setMessages(msgs);
      if (runs[0]) {
        setLatestRunId(runs[0].id);
      }
    } else {
      setMessages((prev) => (prev.length > 0 ? [] : prev));
      setLatestRunId(undefined);
    }
  }, [runs]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || !activeSessionId) return;

    const userMsg: Message = {
      id: `temp-${Date.now()}-user`,
      sender: 'user',
      content: inputQuery,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    const promptToSend = inputQuery;
    setInputQuery('');

    // Trigger API execution run
    runAgent.mutate(promptToSend, {
      onSuccess: (data) => {
        setLatestRunId(data.id);
      },
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch text-left h-[calc(100vh-140px)]">
      
      {/* 1. Left Sidebar: Agent Selection (col-span-3) */}
      <div className="lg:col-span-3 rounded-xl border border-white/5 bg-neutral-950/40 p-4 flex flex-col justify-between overflow-y-auto">
        <div className="space-y-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block mb-4">Choose Agent Sandbox</span>
          
          <div className="space-y-2.5">
            {agents.map((ag) => (
              <button
                key={ag.id}
                onClick={() => {
                  setSelectedAgentId(ag.id);
                  setActiveSessionId('');
                }}
                className={cn(
                  'w-full flex items-center gap-3 p-3 rounded-lg border text-left cursor-pointer transition-all',
                  selectedAgentId === ag.id 
                    ? 'border-violet-500 bg-violet-600/5 text-white' 
                    : 'border-white/5 bg-neutral-900/20 text-neutral-400 hover:text-white hover:border-white/10'
                )}
              >
                <AgentAvatar name={ag.name} avatarColor={ag.avatar_color} size="sm" />
                <div className="truncate">
                  <span className="text-xs font-semibold block truncate leading-tight">{ag.name}</span>
                  <span className="text-[8px] font-mono text-neutral-500 uppercase block mt-0.5">{ag.agent_type}</span>
                </div>
              </button>
            ))}
            {agents.length === 0 && (
              <span className="text-xs text-neutral-500 block p-3 text-center">No active agents. Create one first.</span>
            )}
          </div>
        </div>
      </div>

      {/* 2. Center Panel: Chat Interface (col-span-5) */}
      <div className="lg:col-span-5 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col justify-between overflow-hidden">
        {/* Chat Header info */}
        <div className="p-4 border-b border-white/5 bg-neutral-950/60 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <Bot className="w-5 h-5 text-violet-400" />
            <div>
              <h4 className="text-xs font-bold text-white">{agent ? agent.name : 'Select Agent Sandbox'}</h4>
              <span className="text-[9px] text-neutral-500 font-mono block mt-0.5">PLAYGROUND SESSION ACTIVE</span>
            </div>
          </div>
        </div>

        {/* Message Logs Feed */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center p-4 gap-2 text-neutral-500 select-none">
              <MessageSquare className="w-8 h-8 opacity-25" />
              <span>Send a message to begin execution testing.</span>
            </div>
          )}

          {messages.map((msg) => (
            <div 
              key={msg.id}
              className={cn(
                'flex flex-col max-w-[85%] rounded-xl p-3.5 border text-left leading-relaxed',
                msg.sender === 'user'
                  ? 'bg-neutral-900 border-white/5 text-neutral-200 self-end ml-auto'
                  : 'bg-violet-600/5 border-violet-500/10 text-white self-start'
              )}
            >
              <div className="flex justify-between items-center text-[8px] text-neutral-500 mb-1.5 font-mono select-none">
                <span className="font-bold">{msg.sender === 'user' ? 'USER QUERY' : 'AGENT OUT'}</span>
                <span>{msg.timestamp}</span>
              </div>
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {/* Latency and cost metrics indicators */}
              {msg.sender === 'agent' && (msg.latency || msg.tokens) && (
                <div className="flex items-center gap-3 border-t border-white/5 pt-2.5 mt-2.5 text-[8px] font-mono text-neutral-500 select-none">
                  {msg.latency && <span className="flex items-center gap-1"><Activity className="w-3 h-3 text-violet-400" /> {msg.latency}ms</span>}
                  {msg.tokens && <span className="flex items-center gap-1"><BrainCircuit className="w-3 h-3 text-cyan-400" /> {msg.tokens} tokens</span>}
                  {msg.cost && <span className="flex items-center gap-1"><DollarSign className="w-3 h-3 text-amber-400" /> ${msg.cost.toFixed(5)}</span>}
                </div>
              )}
            </div>
          ))}

          {/* Loading loader */}
          {runAgent.isPending && (
            <div className="bg-violet-600/5 border border-violet-500/10 rounded-xl p-3.5 text-left text-white self-start max-w-[85%] animate-pulse">
              <span className="text-[8px] font-bold text-neutral-500 font-mono block mb-1">AGENT STREAMING...</span>
              <span className="text-neutral-400">Executing pipeline loop iterations...</span>
            </div>
          )}
        </div>

        {/* Input form */}
        <form onSubmit={handleSend} className="p-3 bg-neutral-950 border-t border-white/5 flex gap-2 shrink-0">
          <input
            type="text"
            required
            disabled={!activeSessionId || runAgent.isPending}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder={activeSessionId ? "Ask the agent a target question..." : "Select an agent first to establish session thread..."}
            className="flex-1 px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-violet-500 transition-colors"
          />
          <Button
            type="submit"
            variant="violet"
            disabled={!inputQuery.trim() || runAgent.isPending}
            className="w-10 h-10 rounded-lg p-0 flex items-center justify-center cursor-pointer shrink-0"
          >
            <Send className="w-4 h-4 text-white" />
          </Button>
        </form>
      </div>

      {/* 3. Right Sidebar: Live Logs Console & Memory Vault (col-span-4) */}
      <div className="lg:col-span-4 space-y-6 overflow-y-auto">
        <ExecutionLog logs={logs} isLoading={runAgent.isPending} className="h-[300px]" />

        {/* Dynamic Memory States display */}
        <div className="p-5 rounded-xl border border-white/5 bg-neutral-950/40 text-left space-y-4">
          <div className="flex items-center gap-2 border-b border-white/5 pb-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Live Session Memory</span>
          </div>

          {agent?.memory_enabled ? (
            <div className="space-y-3.5">
              <div className="p-3 bg-neutral-900 border border-white/5 rounded-lg text-[10px] font-mono text-neutral-400">
                <span className="text-violet-400 block font-bold mb-1">BRAND IDENTITY VOICE:</span>
                "Maintain corporate tone matching Viptant guideline standards."
              </div>

              <div className="p-3 bg-neutral-900 border border-white/5 rounded-lg text-[10px] font-mono text-neutral-400">
                <span className="text-cyan-400 block font-bold mb-1">USER DETAILS RETRIEVED:</span>
                "Authenticated: John Doe, Organization: Acme Corp."
              </div>
            </div>
          ) : (
            <div className="text-[10px] text-neutral-500 py-4 text-center">
              Session memory is disabled for this agent definition.
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

export function AgentSandboxPage() {
  return (
    <React.Suspense fallback={<div className="text-neutral-500 text-xs py-8 text-center animate-pulse">Loading agent sandbox...</div>}>
      <AgentPlaygroundContent />
    </React.Suspense>
  );
}

export default AgentSandboxPage;
