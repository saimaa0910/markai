'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAgentSessions, useAgentRuns } from '@/features/agents/hooks';
import { RunTimeline } from '@/features/agents/components/timeline';
import { Button } from '@/components/ui/button';
import { History, Activity, Clock, Play, RefreshCw, HelpCircle } from 'lucide-react';
import { cn } from '@eaimos/shared';

export default function AgentRunsPage() {
  const router = useRouter();
  const { sessions, isLoading: loadingSessions } = useAgentSessions(1, 100);
  const [selectedSessionId, setSelectedSessionId] = React.useState('');

  const { runs, isLoading: loadingRuns, refetch } = useAgentRuns(selectedSessionId || undefined);

  React.useEffect(() => {
    if (sessions.length > 0 && !selectedSessionId) {
      setSelectedSessionId(sessions[0].id);
    }
  }, [sessions, selectedSessionId]);

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-white/5 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <History className="w-5 h-5 text-violet-400" /> Runs History
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            Audit historical outputs, latency profiles, and execution logs.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={() => refetch()}
          className="h-10 text-xs font-semibold gap-1.5 border-white/5 text-neutral-300 hover:text-white"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Sidebar: Session select list (col-span-4) */}
        <div className="lg:col-span-4 space-y-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">Active Session Threads</span>

          {loadingSessions ? (
            <span className="text-xs text-neutral-500 block p-3 text-center">Loading sessions...</span>
          ) : sessions.length === 0 ? (
            <span className="text-xs text-neutral-500 block p-3 text-center">No active playground sessions</span>
          ) : (
            <div className="space-y-2.5">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedSessionId(s.id)}
                  className={cn(
                    'w-full p-3.5 rounded-lg border text-left cursor-pointer transition-all text-xs font-mono',
                    selectedSessionId === s.id
                      ? 'border-violet-500 bg-violet-600/5 text-white'
                      : 'border-white/5 bg-neutral-900/20 text-neutral-400 hover:text-white hover:border-white/10'
                  )}
                >
                  <span className="font-semibold block text-white truncate">{s.title}</span>
                  <span className="text-[8px] text-neutral-500 block mt-1">ID: {s.id.slice(0, 8)}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Execution Timeline (col-span-8) */}
        <div className="lg:col-span-8 space-y-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">Execution Timeline Steps</span>

          {loadingRuns ? (
            <div className="py-20 text-center text-neutral-500 flex flex-col items-center gap-3">
              <span className="animate-pulse">Loading runs history...</span>
            </div>
          ) : !selectedSessionId ? (
            <div className="py-20 text-center text-neutral-500 border border-white/5 bg-neutral-950/20 rounded-2xl flex flex-col items-center justify-center p-4 gap-2">
              <HelpCircle className="w-8 h-8 opacity-20" />
              <span className="text-xs">Select a session thread to inspect runs history</span>
            </div>
          ) : runs.length === 0 ? (
            <div className="py-20 text-center text-neutral-500 border border-white/5 bg-neutral-950/20 rounded-2xl flex flex-col items-center justify-center p-4 gap-2">
              <Activity className="w-8 h-8 opacity-20" />
              <span className="text-xs">No execution runs logged on this session thread yet.</span>
            </div>
          ) : (
            <div className="space-y-6">
              {runs.map((run) => (
                <div key={run.id} className="p-5 rounded-xl border border-white/6 bg-neutral-950/40">
                  <div className="flex justify-between items-center border-b border-white/5 pb-3.5 mb-5 font-mono text-[10px] text-neutral-500">
                    <span>RUN ID: {run.id.slice(0, 8)}</span>
                    <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Latency: {run.latency_ms || '0'}ms</span>
                  </div>
                  <RunTimeline run={run} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
