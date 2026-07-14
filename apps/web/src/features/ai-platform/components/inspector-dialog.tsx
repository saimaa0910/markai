import * as React from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  Terminal, ShieldCheck, ShieldAlert, Cpu, Database, 
  Clock, DollarSign, Key, CpuIcon, Layers, FileText 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';

interface InspectorDialogProps {
  isOpen: boolean;
  onClose: () => void;
  requestLog: any;
}

export function InspectorDialog({ isOpen, onClose, requestLog }: InspectorDialogProps) {
  const [activeTab, setActiveTab] = React.useState<'request' | 'prompt'>('request');

  if (!requestLog) return null;

  const mockHeaders = {
    'content-type': 'application/json',
    'x-request-id': requestLog.id,
    'authorization': 'Bearer viptant_sec_*****',
    'accept': 'text/event-stream',
  };

  const mockPayload = {
    model: requestLog.model_name,
    messages: [
      { role: 'system', content: 'You are an autonomous AI Agent copywriter.' },
      { role: 'user', content: 'Create a dynamic call-to-action variant targeting SaaS conversion optimization.' }
    ],
    temperature: 0.7,
    max_tokens: 1024,
    stream: true,
  };

  const promptSizeChars = 124;
  const promptTokensCount = requestLog.prompt_tokens || 31;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={`Request Trace: ${requestLog.id.slice(0, 12)}`}
      className="max-w-2xl"
    >
      <div className="flex flex-col gap-4 mt-1">
        {/* Toggle Inspector Type */}
        <div className="flex items-center bg-neutral-900 border border-white/5 rounded-xl p-0.5 text-xs font-semibold self-start">
          <button
            onClick={() => setActiveTab('request')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === 'request' ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
            }`}
          >
            Request Inspector
          </button>
          <button
            onClick={() => setActiveTab('prompt')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === 'prompt' ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
            }`}
          >
            Prompt Inspector
          </button>
        </div>

        {activeTab === 'request' ? (
          <div className="flex flex-col gap-4">
            {/* KPI grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-1">
                <span className="text-[9px] text-neutral-500 uppercase font-semibold">Latency</span>
                <span className="text-amber-400 font-bold">{requestLog.latency_ms}ms</span>
              </div>
              <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-1">
                <span className="text-[9px] text-neutral-500 uppercase font-semibold">Calculated Cost</span>
                <span className="text-emerald-400 font-bold">${Number(requestLog.cost_usd).toFixed(5)}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-1">
                <span className="text-[9px] text-neutral-500 uppercase font-semibold">Tokens</span>
                <span className="text-white font-bold">{requestLog.total_tokens} t</span>
              </div>
              <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-1">
                <span className="text-[9px] text-neutral-500 uppercase font-semibold">Status code</span>
                <Badge variant={requestLog.status === 'success' ? 'emerald' : 'rose'} size="sm" dot>
                  {requestLog.status === 'success' ? '200 OK' : '500 ERR'}
                </Badge>
              </div>
            </div>

            {/* Request parameters */}
            <Card className="flex flex-col gap-3 p-4 bg-neutral-950/20">
              <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-violet-400" /> Gateway Parameters
              </span>
              <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                <div className="flex justify-between border-b border-white/5 pb-1.5">
                  <span className="text-neutral-500">Provider:</span>
                  <span className="text-neutral-200 capitalize">{requestLog.provider}</span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-1.5">
                  <span className="text-neutral-500">Model Name:</span>
                  <span className="text-neutral-200">{requestLog.model_name}</span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-1.5">
                  <span className="text-neutral-500">Temperature:</span>
                  <span className="text-neutral-200">0.70</span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-1.5">
                  <span className="text-neutral-500">Max Tokens:</span>
                  <span className="text-neutral-200">1024</span>
                </div>
              </div>
            </Card>

            {/* Headers and Payload */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="p-4 flex flex-col gap-2 bg-neutral-950/20">
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
                  <Key className="w-3.5 h-3.5 text-violet-400" /> Connection Headers
                </span>
                <pre className="p-2.5 rounded bg-black/40 border border-white/5 text-[10px] font-mono text-neutral-400 max-h-[120px] overflow-y-auto">
                  {JSON.stringify(mockHeaders, null, 2)}
                </pre>
              </Card>

              <Card className="p-4 flex flex-col gap-2 bg-neutral-950/20">
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
                  <Terminal className="w-3.5 h-3.5 text-violet-400" /> Request Payload
                </span>
                <pre className="p-2.5 rounded bg-black/40 border border-white/5 text-[10px] font-mono text-neutral-400 max-h-[120px] overflow-y-auto">
                  {JSON.stringify(mockPayload, null, 2)}
                </pre>
              </Card>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {/* Stats row */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex items-center justify-between">
                <span className="text-neutral-500">Prompt Size:</span>
                <span className="text-white font-bold">{promptSizeChars} chars</span>
              </div>
              <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex items-center justify-between">
                <span className="text-neutral-500">Prompt Tokens:</span>
                <span className="text-violet-400 font-bold">{promptTokensCount} t</span>
              </div>
            </div>

            {/* Prompt panels */}
            <div className="flex flex-col gap-3">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">System Instructions</label>
                <div className="p-3 rounded-lg bg-black/40 border border-white/5 text-xs text-neutral-300 font-mono leading-relaxed">
                  You are an autonomous AI Agent copywriter.
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">User Input Prompt</label>
                <div className="p-3 rounded-lg bg-black/40 border border-white/5 text-xs text-neutral-300 font-mono leading-relaxed">
                  Create a dynamic call-to-action variant targeting SaaS conversion optimization.
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Inference Output Response</label>
                <div className="p-3 rounded-lg bg-black/40 border border-emerald-500/10 bg-emerald-500/5 text-xs text-neutral-300 leading-relaxed">
                  {requestLog.status === 'success' ? (
                    'Unlock autonomous scale today. Deploy AI workflows in 2 clicks and slash campaign latencies instantly. Start Free Trial.'
                  ) : (
                    <span className="text-rose-400 font-mono">
                      ERROR: Endpoint connection fail. {requestLog.error_message || 'Socket timeout.'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="border-t border-white/5 pt-3.5 flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="text-xs border-white/5"
          >
            Close Inspector
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
