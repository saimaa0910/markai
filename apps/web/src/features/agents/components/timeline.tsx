'use client';

import * as React from 'react';
import { 
  Play, CheckCircle2, AlertCircle, Clock, Database, 
  Terminal, Search, Cpu, MessageSquare, AlertTriangle, ArrowRight, ShieldCheck 
} from 'lucide-react';
import { AgentRun, AgentLog } from '../types';
import { cn } from '@eaimos/shared';

interface RunTimelineProps {
  run: AgentRun | null;
  className?: string;
}

export function RunTimeline({ run, className }: RunTimelineProps) {
  if (!run) {
    return (
      <div className="text-xs text-neutral-500 p-8 border border-white/5 bg-neutral-950/40 rounded-xl text-center">
        No execution trace loaded
      </div>
    );
  }

  // Generate list of steps representing execution stages
  const steps = [
    { name: 'Run Triggered', desc: `User Input: "${run.user_input}"`, status: 'COMPLETED', icon: Play },
    { name: 'Context Formulation', desc: `Analyzed workspace variables and parameters context.`, status: 'COMPLETED', icon: Database },
    ...(run.tool_calls || []).map((t, idx) => ({
      name: `Call Tool: ${t.name || 'External API'}`,
      desc: `Arguments: ${JSON.stringify(t.arguments || '{}')}`,
      status: 'COMPLETED',
      icon: Search,
    })),
    {
      name: run.status === 'COMPLETED' ? 'Execution Finished' : run.status === 'FAILED' ? 'Execution Errored' : 'Processing Output',
      desc: run.status === 'COMPLETED' 
        ? `Output generated in ${run.iterations} steps.` 
        : run.status === 'FAILED' 
        ? `Error: ${run.error_message || 'System crash'}` 
        : `Running pipeline loop iterations...`,
      status: run.status,
      icon: run.status === 'COMPLETED' ? CheckCircle2 : run.status === 'FAILED' ? AlertCircle : ActivityIcon,
    },
  ];

  return (
    <div className={cn('space-y-6 text-left relative before:absolute before:top-2 before:bottom-2 before:left-[15px] before:w-px before:bg-white/10', className)}>
      {steps.map((s, idx) => {
        const Icon = s.icon;
        return (
          <div key={s.name + idx} className="flex gap-4 items-start relative">
            <div className={cn(
              'w-8 h-8 rounded-full border bg-neutral-950 flex items-center justify-center shrink-0 z-10',
              s.status === 'COMPLETED' ? 'border-emerald-500/30 text-emerald-400' :
              s.status === 'FAILED' ? 'border-rose-500/30 text-rose-400' : 'border-violet-500/30 text-violet-400 animate-pulse'
            )}>
              <Icon className="w-3.5 h-3.5" />
            </div>

            <div className="flex-1 p-4 rounded-xl border border-white/5 bg-neutral-950/40">
              <div className="flex justify-between items-start gap-4">
                <span className="text-xs font-bold text-white leading-none">{s.name}</span>
                <span className={cn(
                  'text-[9px] font-mono font-bold uppercase tracking-wider',
                  s.status === 'COMPLETED' ? 'text-emerald-400' :
                  s.status === 'FAILED' ? 'text-rose-400' : 'text-violet-400'
                )}>
                  {s.status}
                </span>
              </div>
              <p className="text-[10px] text-neutral-400 leading-relaxed mt-2.5 whitespace-pre-wrap break-all font-mono">
                {s.desc}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface ExecutionLogProps {
  logs: AgentLog[];
  isLoading?: boolean;
  className?: string;
}

export function ExecutionLog({ logs, isLoading, className }: ExecutionLogProps) {
  const [filter, setFilter] = React.useState<'ALL' | 'INFO' | 'WARNING' | 'ERROR'>('ALL');
  const [search, setSearch] = React.useState('');

  const filteredLogs = logs.filter((l) => {
    const matchesFilter = filter === 'ALL' || l.level.toUpperCase() === filter;
    const matchesSearch = l.content.toLowerCase().includes(search.toLowerCase()) || 
                          l.step_type.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const levelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR': return 'text-rose-400';
      case 'WARNING': return 'text-amber-400';
      case 'INFO': return 'text-violet-400';
      default: return 'text-neutral-400';
    }
  };

  return (
    <div className={cn('flex flex-col rounded-xl border border-white/8 bg-neutral-950/40 overflow-hidden font-mono text-xs text-left h-[450px]', className)}>
      {/* Header bar controls */}
      <div className="p-3 bg-neutral-950 border-b border-white/5 flex flex-col sm:flex-row gap-3 justify-between items-center shrink-0">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-violet-400" />
          <span className="font-bold text-xs text-white">Execution Console</span>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter content logs..."
            className="px-2.5 py-1 text-[11px] rounded bg-neutral-900 border border-white/5 text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 w-full sm:w-40"
          />

          <div className="flex bg-neutral-900 rounded border border-white/5 p-0.5 shrink-0">
            {(['ALL', 'INFO', 'WARNING', 'ERROR'] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilter(lvl)}
                className={cn(
                  'px-2 py-0.5 rounded text-[9px] font-bold tracking-wide transition-colors cursor-pointer',
                  filter === lvl ? 'bg-neutral-800 text-white' : 'text-neutral-500 hover:text-neutral-300'
                )}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Logs Display Scroll list */}
      <div className="flex-1 overflow-auto p-4 space-y-3 font-mono text-[10px]">
        {isLoading ? (
          <div className="h-full flex items-center justify-center text-neutral-500">
            <span className="animate-pulse">Fetching execution logs...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-neutral-500">
            <span>No matching log traces found.</span>
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div key={log.id} className="border-b border-white/2 pb-2 last:border-0 hover:bg-white/2 transition-colors">
              <div className="flex items-center gap-2 text-[9px] text-neutral-500 mb-1">
                <span className={cn('font-bold font-mono uppercase', levelColor(log.level))}>
                  [{log.level}]
                </span>
                <span>·</span>
                <span className="text-violet-400 font-bold">{log.step_type}</span>
                {log.meta_data && (
                  <>
                    <span>·</span>
                    <span className="text-neutral-600 truncate max-w-[200px]" title={JSON.stringify(log.meta_data)}>
                      {JSON.stringify(log.meta_data)}
                    </span>
                  </>
                )}
              </div>
              <p className="text-neutral-300 leading-relaxed whitespace-pre-wrap">{log.content}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function ActivityIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
      className={cn('w-3.5 h-3.5', props.className)}
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}
