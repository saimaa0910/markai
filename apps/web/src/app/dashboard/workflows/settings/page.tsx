'use client';

import * as React from 'react';
import { SlidersHorizontal, ShieldAlert, Key, Clipboard, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function WorkflowSettingsPage() {
  const [apiKey, setApiKey] = React.useState('vt_wf_live_839a82fbc0429fde01bce7');
  const [concurrencyLimit, setConcurrencyLimit] = React.useState(10);
  const [retryDelay, setRetryDelay] = React.useState(30);
  const [saving, setSaving] = React.useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      alert('Workflow settings saved successfully.');
    }, 800);
  };

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    alert('API Key copied to clipboard!');
  };

  return (
    <div className="space-y-6 text-left max-w-3xl mx-auto">
      {/* Header */}
      <div className="border-b border-white/5 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-violet-400" /> Orchestrator Settings
        </h2>
        <p className="text-xs text-neutral-400 mt-1">
          Manage inbound webhook trigger tokens, rate throttling limits, and retry policies.
        </p>
      </div>

      {/* Settings Form */}
      <form onSubmit={handleSave} className="p-6 rounded-xl border border-white/10 bg-neutral-950/40 glass space-y-6">
        
        {/* Webhook credentials */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Inbound Webhook Trigger Authorization Token</label>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={apiKey}
              className="flex-1 px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none font-mono"
            />
            <Button
              type="button"
              variant="outline"
              onClick={handleCopyKey}
              className="h-10 text-xs border-white/5 gap-1.5 text-neutral-300 hover:text-white shrink-0 cursor-pointer"
            >
              <Clipboard className="w-4 h-4" /> Copy Key
            </Button>
          </div>
          <span className="text-[9px] text-neutral-500 block leading-relaxed">
            Attach this token in HTTP header `Authorization: Bearer &lt;key&gt;` when calling `/api/v1/workflows/webhooks/trigger`
          </span>
        </div>

        {/* Concurrency limits */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Max Concurrently Active Runs</label>
            <input
              type="number"
              value={concurrencyLimit}
              onChange={(e) => setConcurrencyLimit(parseInt(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Default Retry Backoff Delay (seconds)</label>
            <input
              type="number"
              value={retryDelay}
              onChange={(e) => setRetryDelay(parseInt(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none font-mono"
            />
          </div>
        </div>

        <div className="border-t border-white/5 pt-6 mt-6 flex justify-end">
          <Button
            type="submit"
            variant="violet"
            className="h-10 text-xs font-semibold gap-1.5"
            isLoading={saving}
          >
            <CheckCircle2 className="w-4 h-4" /> Save Configuration
          </Button>
        </div>

      </form>
    </div>
  );
}
