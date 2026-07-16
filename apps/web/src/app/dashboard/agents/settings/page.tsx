'use client';

import * as React from 'react';
import { SlidersHorizontal, ShieldAlert, Cpu, Sparkles, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function AgentSettingsPage() {
  const [defaultModel, setDefaultModel] = React.useState('gemini-2.5-pro');
  const [rateLimit, setRateLimit] = React.useState(100);
  const [budgetCeiling, setBudgetCeiling] = React.useState(5.0);
  const [sandboxEnabled, setSandboxEnabled] = React.useState(true);
  const [saving, setSaving] = React.useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      alert('Platform settings saved successfully.');
    }, 800);
  };

  return (
    <div className="space-y-6 text-left max-w-3xl mx-auto">
      {/* Header */}
      <div className="border-b border-white/5 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-violet-400" /> Platform Agent Settings
        </h2>
        <p className="text-xs text-neutral-400 mt-1">
          Manage system boundaries, queue rate limits, and default routing rules.
        </p>
      </div>

      {/* Form config panel */}
      <form onSubmit={handleSave} className="p-6 rounded-xl border border-white/10 bg-neutral-950/40 glass space-y-6">
        
        {/* Default Model */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Default LLM Model Override</label>
          <select
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 font-mono"
          >
            <option value="gemini-2.5-pro">Google Gemini 2.5 Pro</option>
            <option value="claude-3-5-sonnet">Anthropic Claude 3.5 Sonnet</option>
            <option value="gpt-4o">OpenAI GPT-4o</option>
          </select>
        </div>

        {/* Rate limits inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Default Rate Limit Throttle (req/min)</label>
            <input
              type="number"
              value={rateLimit}
              onChange={(e) => setRateLimit(parseInt(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Safety Budget Ceiling Cap ($ / Day)</label>
            <input
              type="number"
              step="0.5"
              value={budgetCeiling}
              onChange={(e) => setBudgetCeiling(parseFloat(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 font-mono"
            />
          </div>
        </div>

        {/* Sandbox toggle controls */}
        <div className="flex justify-between items-center border-t border-white/5 pt-4">
          <div>
            <span className="text-xs font-semibold text-white block">Strict Sandbox Executions</span>
            <span className="text-[10px] text-neutral-500 block mt-0.5">Force all tool executions to run inside safe container registries.</span>
          </div>

          <button
            type="button"
            onClick={() => setSandboxEnabled(!sandboxEnabled)}
            className={`w-10 h-5.5 rounded-full p-1 transition-colors cursor-pointer outline-none flex items-center ${
              sandboxEnabled ? 'bg-violet-600' : 'bg-neutral-800 border border-white/5'
            }`}
          >
            <div
              className={`w-3.5 h-3.5 rounded-full bg-white transition-transform duration-200 ${
                sandboxEnabled ? 'translate-x-4.5' : 'translate-x-0'
              }`}
            />
          </button>
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
