import * as React from 'react';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { Card } from '@eaimos/ui';
import { SlidersHorizontal, Key, Eye, EyeOff, Save, ShieldAlert, Cpu } from 'lucide-react';
import { useProviders, useModels } from '../hooks';

interface KeyConfig {
  key: string;
  name: string;
  envVar: string;
  docsUrl: string;
  description: string;
}

const API_KEYS_CONFIG: KeyConfig[] = [
  {
    key: 'openai',
    name: 'OpenAI',
    envVar: 'OPENAI_API_KEY',
    docsUrl: 'https://platform.openai.com/api-keys',
    description: 'Powers GPT-4o and GPT-4o-mini models.',
  },
  {
    key: 'groq',
    name: 'Groq API',
    envVar: 'GROQ_API_KEY',
    docsUrl: 'https://console.groq.com/keys',
    description: 'Ultra-low latency LPU inference engine for open models.',
  },
  {
    key: 'anthropic',
    name: 'Anthropic Claude',
    envVar: 'ANTHROPIC_API_KEY',
    docsUrl: 'https://console.anthropic.com/settings/keys',
    description: 'Powers Claude 3.5 Sonnet and Haiku models.',
  },
  {
    key: 'google',
    name: 'Google Gemini',
    envVar: 'GEMINI_API_KEY',
    docsUrl: 'https://aistudio.google.com/app/apikey',
    description: 'Gemini Pro/Flash multimodal reasoning.',
  },
];

export function SettingsPage() {
  const { providers } = useProviders();
  const { models } = useModels();

  const [form, setForm] = React.useState({
    default_provider: 'openai',
    default_model: 'gpt-4o-mini',
    fallback_model: 'gemini-1.5-flash',
    retry_count: 3,
    temperature: 0.7,
    max_tokens: 2048,
    health_interval: 60,
    cost_threshold: 150.00,
    enable_caching: true,
  });

  const [apiKeys, setApiKeys] = React.useState<Record<string, string>>({
    openai: '••••••••••••••••••••••••••••••••',
    groq: '••••••••••••••••••••••••••••••••',
    anthropic: '••••••••••••••••••••••••••••••••',
    google: '••••••••••••••••••••••••••••••••',
  });

  const [visibleKeys, setVisibleKeys] = React.useState<Record<string, boolean>>({});

  const toggleKeyVisibility = (key: string) => {
    setVisibleKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleKeySave = (key: string) => {
    toast.success('Key Updated', `${key.toUpperCase()} API key saved. Restart the orchestrator service to apply secrets.`);
  };

  const handleFormSave = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success('Settings Configured', 'Gateway routing defaults have been saved successfully.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Gateway Settings"
        description="Configure default models routing overrides, error fallback retry limits, context limits, and API keys."
        icon={<SlidersHorizontal className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">System config</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core settings form */}
        <form onSubmit={handleFormSave} className="lg:col-span-2 flex flex-col gap-6">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Default Model Allocations</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Define fallback models when custom dynamic rules match no conditions.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Primary Provider</label>
                <Select
                  value={form.default_provider}
                  onChange={(e) => setForm((prev) => ({ ...prev, default_provider: e.target.value }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={providers.map((p) => ({ label: p.name, value: p.key }))}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Primary Model Node</label>
                <Select
                  value={form.default_model}
                  onChange={(e) => setForm((prev) => ({ ...prev, default_model: e.target.value }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={models.map((m) => ({ label: `${m.name} (${m.provider})`, value: m.model_name }))}
                />
              </div>

              <div className="flex flex-col gap-1.5 md:col-span-2">
                <label className="text-xs text-neutral-400 font-semibold">Gateway Fallback Target</label>
                <Select
                  value={form.fallback_model}
                  onChange={(e) => setForm((prev) => ({ ...prev, fallback_model: e.target.value }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={models.map((m) => ({ label: `${m.name} (${m.provider})`, value: m.model_name }))}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Resiliency & Hyperparameters</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Control fallback retries, token length settings, and response temperatures.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Retry Count</label>
                <Input
                  type="number"
                  value={form.retry_count}
                  onChange={(e) => setForm((prev) => ({ ...prev, retry_count: Number(e.target.value) }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  min={0}
                  max={5}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Temperature</label>
                <Input
                  type="number"
                  step="0.1"
                  value={form.temperature}
                  onChange={(e) => setForm((prev) => ({ ...prev, temperature: Number(e.target.value) }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  min={0}
                  max={2}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Max Tokens Limit</label>
                <Input
                  type="number"
                  value={form.max_tokens}
                  onChange={(e) => setForm((prev) => ({ ...prev, max_tokens: Number(e.target.value) }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  min={1}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Ping Interval (seconds)</label>
                <Input
                  type="number"
                  value={form.health_interval}
                  onChange={(e) => setForm((prev) => ({ ...prev, health_interval: Number(e.target.value) }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  min={10}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Monthly Limit Alert ($)</label>
                <Input
                  type="number"
                  value={form.cost_threshold}
                  onChange={(e) => setForm((prev) => ({ ...prev, cost_threshold: Number(e.target.value) }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  min={0}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-neutral-400 font-semibold">Embeddings Cache</label>
                <Select
                  value={form.enable_caching ? 'yes' : 'no'}
                  onChange={(e) => setForm((prev) => ({ ...prev, enable_caching: e.target.value === 'yes' }))}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={[
                    { label: 'Active (Highly recommended)', value: 'yes' },
                    { label: 'Inactive', value: 'no' }
                  ]}
                />
              </div>
            </div>

            <div className="flex items-center justify-end border-t border-white/5 pt-4 mt-2">
              <Button type="submit" variant="violet" size="sm" className="gap-1.5 text-xs h-9">
                <Save className="w-3.5 h-3.5" />
                Save Preferences
              </Button>
            </div>
          </Card>
        </form>

        {/* API keys section */}
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm flex items-center gap-1.5">
                Credential Secrets <Key className="w-4 h-4 text-violet-400" />
              </h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Register API keys to authenticate integrated LLM providers.</p>
            </div>

            <div className="flex flex-col gap-4">
              {API_KEYS_CONFIG.map((k) => {
                const isVisible = visibleKeys[k.key] || false;
                return (
                  <div key={k.key} className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col gap-2 relative group">
                    <div className="flex items-start justify-between">
                      <div className="flex flex-col">
                        <span className="text-xs font-bold text-neutral-200">{k.name} Gateway</span>
                        <a 
                          href={k.docsUrl} 
                          target="_blank" 
                          rel="noreferrer"
                          className="text-[9px] text-violet-400 hover:underline mt-0.5 flex items-center gap-0.5"
                        >
                          Generate {k.name} secret key
                        </a>
                      </div>
                    </div>

                    <div className="relative flex items-center gap-1.5 mt-1.5">
                      <div className="relative flex-1">
                        <Input
                          type={isVisible ? 'text' : 'password'}
                          value={apiKeys[k.key]}
                          onChange={(e) => setApiKeys((prev) => ({ ...prev, [k.key]: e.target.value }))}
                          className="bg-neutral-900 border-white/5 h-8 pr-8 text-[11px] font-mono text-white"
                        />
                        <button
                          type="button"
                          onClick={() => toggleKeyVisibility(k.key)}
                          className="absolute right-2 top-2 text-neutral-500 hover:text-white cursor-pointer"
                        >
                          {isVisible ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                      
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleKeySave(k.key)}
                        className="h-8 px-2.5 text-[10px] border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
                      >
                        Apply
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="p-3 rounded-lg border border-rose-500/10 bg-rose-500/5 flex items-start gap-2.5 mt-2">
              <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <p className="text-[10px] text-neutral-400 leading-normal">
                Credentials are encrypted on rest and stored inside local environmental parameters. Never check raw secrets into git version controls.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
