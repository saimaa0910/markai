import * as React from 'react';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { Card } from '@eaimos/ui';
import { SlidersHorizontal, Key, Eye, EyeOff, Save, ShieldAlert, Cpu, Loader2, RefreshCw } from 'lucide-react';
import { useProviders, useModels } from '../hooks';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';

interface KeyConfig {
  key: string;
  name: string;
  envVar: string;
  docsUrl: string;
  description: string;
}

const API_KEYS_CONFIG: KeyConfig[] = [
  {
    key: 'groq',
    name: 'Groq API',
    envVar: 'GROQ_API_KEY',
    docsUrl: 'https://console.groq.com/keys',
    description: 'Powers llama-3.3-70b-versatile, llama3-70b, mixtral models.',
  },
  {
    key: 'openai',
    name: 'OpenAI',
    envVar: 'OPENAI_API_KEY',
    docsUrl: 'https://platform.openai.com/api-keys',
    description: 'Powers GPT-4o and GPT-4o-mini models.',
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
  {
    key: 'openrouter',
    name: 'OpenRouter',
    envVar: 'OPENROUTER_API_KEY',
    docsUrl: 'https://openrouter.ai/keys',
    description: 'Access gateway to hundreds of open-source models.',
  },
  {
    key: 'deepseek',
    name: 'DeepSeek',
    envVar: 'DEEPSEEK_API_KEY',
    docsUrl: 'https://platform.deepseek.com/api_keys',
    description: 'Powers DeepSeek-V3 and DeepSeek-R1 reasoning.',
  },
  {
    key: 'mistral',
    name: 'Mistral AI',
    envVar: 'MISTRAL_API_KEY',
    docsUrl: 'https://console.mistral.ai/api-keys',
    description: 'Powers Mistral Large and Mixtral models.',
  },
  {
    key: 'ollama',
    name: 'Local Ollama',
    envVar: 'OLLAMA_API_KEY',
    docsUrl: 'https://github.com/ollama/ollama',
    description: 'Powers local LLMs execution via localhost:11434.',
  },
];

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { providers } = useProviders();
  const { models } = useModels();

  // Load gateway routing settings
  const { data: gatewaySettings, isLoading: loadingSettings } = useQuery({
    queryKey: ['ai-router-settings'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/router/');
      return res.data;
    }
  });

  // Load registered credentials keys
  const { data: registeredKeys = [], isLoading: loadingKeys, refetch: refetchKeys } = useQuery<any[]>({
    queryKey: ['ai-provider-keys'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers/keys/');
      return res.data || [];
    }
  });

  // Load real providers catalog from backend for UUID lookup
  const { data: dbProviders = [] } = useQuery<any[]>({
    queryKey: ['ai-db-providers'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers/');
      return res.data || [];
    }
  });

  const [form, setForm] = React.useState({
    routing_mode: 'cheapest',
    fallback_provider: 'groq',
    is_active: true
  });

  // Sync loaded router settings to form state
  React.useEffect(() => {
    if (gatewaySettings) {
      setForm({
        routing_mode: gatewaySettings.routing_mode || 'cheapest',
        fallback_provider: gatewaySettings.fallback_provider || 'groq',
        is_active: gatewaySettings.is_active !== false
      });
    }
  }, [gatewaySettings]);

  // Keys form input states
  const [apiKeysInput, setApiKeysInput] = React.useState<Record<string, string>>({});
  const [keyScopes, setKeyScopes] = React.useState<Record<string, 'organization' | 'user'>>({});
  const [visibleKeys, setVisibleKeys] = React.useState<Record<string, boolean>>({});

  // Populate key inputs with masked keys from database on load
  React.useEffect(() => {
    const inputs: Record<string, string> = {};
    const scopes: Record<string, 'organization' | 'user'> = {};
    
    API_KEYS_CONFIG.forEach((config) => {
      const matchingKey = registeredKeys.find(
        (rk) => rk.provider_name.toLowerCase() === config.key.toLowerCase()
      );
      inputs[config.key] = matchingKey ? matchingKey.masked_key : '';
      scopes[config.key] = matchingKey?.level === 'user' ? 'user' : 'organization';
    });
    
    setApiKeysInput(inputs);
    setKeyScopes(scopes);
  }, [registeredKeys]);

  // Mutations
  const updateSettingsMutation = useMutation({
    mutationFn: async (updatedForm: typeof form) => {
      const res = await apiClient.put('/ai/router/', updatedForm);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-router-settings'] });
      toast.success('Preferences Saved', 'AI Gateway routing configurations updated.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.message || 'Could not update gateway settings.');
    }
  });

  const saveKeyMutation = useMutation({
    mutationFn: async ({ providerKey, apiKey, level }: { providerKey: string; apiKey: string; level: 'organization' | 'user' }) => {
      // Find provider ID by matching name in dbProviders
      const provObj = dbProviders.find((p) => p.name.toLowerCase() === providerKey.toLowerCase());
      if (!provObj) {
        throw new Error(`Provider ${providerKey} details not loaded yet.`);
      }
      
      const res = await apiClient.post('/ai/providers/keys/', {
        provider_id: provObj.id,
        api_key: apiKey,
        is_active: true,
        level: level
      });
      return res.data;
    },
    onSuccess: () => {
      refetchKeys();
      toast.success('Key Saved', 'Credential parameters registered securely.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.message || 'Could not register credential.');
    }
  });

  const toggleKeyVisibility = (key: string) => {
    setVisibleKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleKeySave = (providerKey: string) => {
    const rawVal = apiKeysInput[providerKey];
    if (!rawVal || rawVal.includes('*****')) {
      toast.error('Validation Error', 'Please enter a valid non-masked key string.');
      return;
    }
    saveKeyMutation.mutate({
      providerKey,
      apiKey: rawVal,
      level: keyScopes[providerKey] || 'organization'
    });
  };

  const handleFormSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettingsMutation.mutate(form);
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Gateway Settings"
        description="Configure default routing modes, fallbacks, and multi-level API credential keys."
        icon={<SlidersHorizontal className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">System config</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: CORE PREFERENCES FORM */}
        <form onSubmit={handleFormSave} className="lg:col-span-2 flex flex-col gap-6">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Default Routing Engine</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Control fallback routing rules when no specific conditions match.</p>
            </div>

            {loadingSettings ? (
              <div className="flex items-center justify-center gap-2 py-10 text-neutral-500 text-xs">
                <Loader2 className="w-4 h-4 animate-spin text-violet-400" /> Loading settings...
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs text-neutral-400 font-semibold">Routing Strategy Mode</label>
                  <Select
                    value={form.routing_mode}
                    onChange={(e) => setForm((prev) => ({ ...prev, routing_mode: e.target.value }))}
                    className="bg-neutral-900 border-white/5 h-9 text-xs"
                    options={[
                      { label: 'Cheapest (Cost optimized)', value: 'cheapest' },
                      { label: 'Fastest (Latency optimized)', value: 'fastest' },
                      { label: 'Highest Quality (Priority-based)', value: 'highest_quality' },
                      { label: 'Balanced (Weighted speed/cost)', value: 'balanced' },
                    ]}
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs text-neutral-400 font-semibold">Primary Fallback Provider</label>
                  <Select
                    value={form.fallback_provider}
                    onChange={(e) => setForm((prev) => ({ ...prev, fallback_provider: e.target.value }))}
                    className="bg-neutral-900 border-white/5 h-9 text-xs"
                    options={providers.map((p) => ({ label: p.name, value: p.key }))}
                  />
                </div>

                <div className="flex flex-col gap-1.5 md:col-span-2">
                  <label className="text-xs text-neutral-400 font-semibold">Gateway Operational Status</label>
                  <Select
                    value={form.is_active ? 'active' : 'inactive'}
                    onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.value === 'active' }))}
                    className="bg-neutral-900 border-white/5 h-9 text-xs"
                    options={[
                      { label: 'Active (Routes traffic)', value: 'active' },
                      { label: 'Bypassed (Mock simulation mode)', value: 'inactive' }
                    ]}
                  />
                </div>
              </div>
            )}

            <div className="flex items-center justify-end border-t border-white/5 pt-4 mt-2">
              <Button type="submit" variant="violet" size="sm" className="gap-1.5 text-xs h-9" disabled={updateSettingsMutation.isPending}>
                {updateSettingsMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Save Preferences
              </Button>
            </div>
          </Card>
        </form>

        {/* RIGHT COLUMN: PROVIDER API KEYS MANAGER */}
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <div className="flex justify-between items-start pb-2 border-b border-white/5">
              <div>
                <h3 className="font-bold text-white text-sm flex items-center gap-1.5">
                  Credential Secrets <Key className="w-4 h-4 text-violet-400" />
                </h3>
                <p className="text-[11px] text-neutral-500 mt-0.5">Register API keys to authenticate integrated providers.</p>
              </div>
              <button onClick={() => refetchKeys()} className="p-1.5 bg-neutral-900 hover:bg-neutral-800 border border-white/5 rounded text-neutral-400 hover:text-white transition-colors">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex flex-col gap-4 max-h-[500px] overflow-y-auto pr-1">
              {loadingKeys ? (
                <div className="flex items-center justify-center gap-2 py-20 text-neutral-500 text-xs">
                  <Loader2 className="w-4 h-4 animate-spin text-violet-400" /> Fetching secure credentials...
                </div>
              ) : (
                API_KEYS_CONFIG.map((k) => {
                  const isVisible = visibleKeys[k.key] || false;
                  const matchingKey = registeredKeys.find(
                    (rk) => rk.provider_name.toLowerCase() === k.key.toLowerCase()
                  );
                  return (
                    <div key={k.key} className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col gap-3 relative group">
                      <div className="flex items-start justify-between">
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-neutral-200">{k.name} Gateway</span>
                          <span className="text-[10px] text-neutral-500 mt-0.5 leading-normal">{k.description}</span>
                        </div>
                        {matchingKey && (
                          <Badge variant="emerald" className="text-[9px] uppercase font-bold px-1.5 py-0">
                            Registered
                          </Badge>
                        )}
                      </div>

                      <div className="flex gap-2 items-center">
                        <div className="flex-1">
                          <span className="text-[10px] text-neutral-400 font-medium">Credential Level Scope</span>
                          <Select
                            value={keyScopes[k.key] || 'organization'}
                            onChange={(e) => setKeyScopes((prev) => ({ ...prev, [k.key]: e.target.value as any }))}
                            className="bg-neutral-900 border-white/5 h-8 text-[11px] mt-1"
                            options={[
                              { label: 'Organization (Shared Workspace key)', value: 'organization' },
                              { label: 'User (My personal key only)', value: 'user' }
                            ]}
                          />
                        </div>
                      </div>

                      <div className="relative flex items-center gap-1.5 mt-1">
                        <div className="relative flex-1">
                          <Input
                            type={isVisible ? 'text' : 'password'}
                            value={apiKeysInput[k.key] || ''}
                            onChange={(e) => setApiKeysInput((prev) => ({ ...prev, [k.key]: e.target.value }))}
                            placeholder={matchingKey ? '••••••••••••••••••••••••••••••••' : 'Enter API Key token...'}
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
                          variant="violet"
                          size="sm"
                          onClick={() => handleKeySave(k.key)}
                          className="h-8 px-3 text-[10px] bg-violet-600 hover:bg-violet-500 font-semibold"
                          disabled={saveKeyMutation.isPending}
                        >
                          Apply
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="p-3 rounded-lg border border-rose-500/10 bg-rose-500/5 flex items-start gap-2.5 mt-2">
              <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <p className="text-[10px] text-neutral-400 leading-normal">
                Credentials are encrypted at rest using AES-256-GCM. Personal user-level keys override organization-level configurations for the active user session.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
