'use client';

import * as React from 'react';
import { useWorkflowExecutions, useExecutionSteps, useWorkflows } from '@/features/workflows/hooks';
import { RefreshCw, Clock, Activity, HelpCircle, Eye, AlertCircle } from 'lucide-react';
import { RunTimeline } from '@/features/agents/components/timeline';
import { Button } from '@/components/ui/button';
import { cn } from '@eaimos/shared';

export default function WorkflowHistoryPage() {
  const { workflows } = useWorkflows(1, 100);
  const [selectedWorkflowId, setSelectedWorkflowId] = React.useState('');

  const { executions, isLoading, refetch } = useWorkflowExecutions(selectedWorkflowId || undefined);
  const [selectedExecId, setSelectedExecId] = React.useState('');

  // Fetch steps details for chosen execution row
  const { steps: executionSteps, isLoading: loadingSteps } = useExecutionSteps(selectedExecId || undefined);

  React.useEffect(() => {
    if (executions.length > 0 && !selectedExecId) {
      setSelectedExecId(executions[0].id);
    }
  }, [executions, selectedExecId]);

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-white/5 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-violet-400" /> Executions History
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            Audit automatic pipeline triggers, error bounds, and resource allocations.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={() => refetch()}
          className="h-10 text-xs font-semibold gap-1.5 border-white/5 text-neutral-300 hover:text-white"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Sync history
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Side: Filter and Execution Lists table (col-span-7) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 justify-between items-center bg-neutral-950/40 p-3 rounded-xl border border-white/5">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">Workflow Filter</span>
            <select
              value={selectedWorkflowId}
              onChange={(e) => {
                setSelectedWorkflowId(e.target.value);
                setSelectedExecId('');
              }}
              className="px-3 py-1.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none max-w-xs font-mono"
            >
              <option value="">All workflows...</option>
              {workflows.map((w) => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>

          {isLoading ? (
            <span className="text-xs text-neutral-500 block p-6 text-center">Fetching executions...</span>
          ) : executions.length === 0 ? (
            <div className="py-20 text-center text-neutral-500 border border-white/5 bg-neutral-950/20 rounded-2xl flex flex-col items-center justify-center p-4 gap-2">
              <Activity className="w-8 h-8 opacity-20" />
              <span className="text-xs">No recorded execution runs found</span>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-white/8 bg-neutral-950/40">
              <table className="w-full border-collapse text-xs text-left font-mono">
                <thead>
                  <tr className="border-b border-white/5 bg-neutral-900/60 text-neutral-400 font-semibold">
                    <th className="p-3">Execution ID</th>
                    <th className="p-3">Trigger Type</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map((e) => (
                    <tr 
                      key={e.id}
                      onClick={() => setSelectedExecId(e.id)}
                      className={cn(
                        'border-b border-white/2 hover:bg-white/2 cursor-pointer transition-colors last:border-0',
                        selectedExecId === e.id && 'bg-violet-600/5'
                      )}
                    >
                      <td className="p-3 font-semibold text-white">{e.id.slice(0, 8)}...</td>
                      <td className="p-3 text-neutral-400">{e.triggered_by ? 'MANUAL' : 'SYSTEM'}</td>
                      <td className="p-3">
                        <span className={cn(
                          'text-[9px] font-bold px-2 py-0.5 rounded border uppercase',
                          e.status === 'COMPLETED' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                          e.status === 'FAILED' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' : 'bg-neutral-900 border-white/5 text-neutral-500'
                        )}>
                          {e.status}
                        </span>
                      </td>
                      <td className="p-3 text-neutral-400">{(e.latency_ms || 0) / 1000}s</td>
                      <td className="p-3 text-right">
                        <button className="p-1 text-violet-400 hover:text-white" title="Inspect timeline">
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right Side: Step Execution details (col-span-5) */}
        <div className="lg:col-span-5 space-y-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">Step Run Timeline</span>

          {!selectedExecId ? (
            <div className="py-20 text-center text-neutral-500 border border-white/5 bg-neutral-950/20 rounded-2xl flex flex-col items-center justify-center p-4 gap-2">
              <HelpCircle className="w-8 h-8 opacity-20" />
              <span className="text-xs">Choose execution run row to inspect details</span>
            </div>
          ) : (
            <div className="p-5 rounded-xl border border-white/6 bg-neutral-950/40 space-y-6">
              <div className="flex justify-between items-center border-b border-white/5 pb-3 font-mono text-[9px] text-neutral-500">
                <span>EXECUTION ID: {selectedExecId.slice(0, 8)}</span>
              </div>

              {loadingSteps ? (
                <span className="text-xs text-neutral-500 animate-pulse block text-center">Fetching execution trace...</span>
              ) : executionSteps.length === 0 ? (
                <span className="text-xs text-neutral-500 block text-center">No trace steps recorded for this run.</span>
              ) : (
                <div className="space-y-4 text-left">
                  {executionSteps.map((step, idx) => (
                    <div key={step.id} className="p-3 rounded-lg border border-white/5 bg-neutral-900/40 flex items-start justify-between font-mono text-[10px]">
                      <div>
                        <span className="font-bold text-white block">{step.step_id}</span>
                        <span className="text-neutral-500 block mt-1">Type: {step.step_type} · Latency: {step.latency_ms}ms</span>
                        {step.error_message && <span className="text-rose-400 block mt-1">Error: {step.error_message}</span>}
                      </div>

                      <span className={cn(
                        'text-[8px] font-bold uppercase px-1.5 py-0.5 rounded border shrink-0',
                        step.status === 'COMPLETED' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                        step.status === 'FAILED' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' : 'bg-neutral-900 border-white/5 text-neutral-500'
                      )}>
                        {step.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
