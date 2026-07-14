'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import { 
  Settings, Key, CreditCard, Radio, ToggleLeft, ToggleRight, 
  Plus, Check, Trash2, Building, Shield, User, Globe, AlertTriangle, Palette
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ThemeSwitcher } from '@/components/ui/theme-switcher';

export default function SettingsDashboard() {
  const queryClient = useQueryClient();
  const { activeOrg, organizations, setOrganizations, setActiveOrg } = useAuthStore();
  const [activeTab, setActiveTab] = React.useState<'org' | 'billing' | 'keys' | 'integrations' | 'appearance'>('org');

  // Org form creation/edit states
  const [editOrgName, setEditOrgName] = React.useState(activeOrg?.name || '');
  const [newOrgName, setNewOrgName] = React.useState('');
  const [creatingOrg, setCreatingOrg] = React.useState(false);

  // API key states
  const [apiKeys, setApiKeys] = React.useState<{ id: string; label: string; token: string; created: string }[]>([
    { id: 'key_1', label: 'Production API Key', token: 'ea_live_••••••••••••••••••••3a9b', created: '2026-07-01' }
  ]);
  const [newKeyLabel, setNewKeyLabel] = React.useState('');

  // Integrations states
  const [integrations, setIntegrations] = React.useState([
    { id: 'slack', name: 'Slack Alerts', desc: 'Push automated campaign performance alerts.', active: true },
    { id: 'gmail', name: 'Gmail Connector', desc: 'Sync customer mailing lists and outbound logs.', active: false },
    { id: 'drive', name: 'Google Drive', desc: 'Ingest collateral documents directly to Knowledge base.', active: false },
    { id: 'openai', name: 'OpenAI Developer Keys', desc: 'Enable secondary completions via custom keys.', active: true }
  ]);

  // Handle Org switch/refresh
  React.useEffect(() => {
    if (activeOrg) {
      setEditOrgName(activeOrg.name);
    }
  }, [activeOrg]);

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setCreatingOrg(true);
    try {
      const res = await apiClient.post('/organizations/', { name: newOrgName });
      const newOrg = res.data;
      
      const updatedOrgs = [...organizations, newOrg];
      setOrganizations(updatedOrgs);
      setActiveOrg(newOrg);
      setNewOrgName('');
      toast.success('Organization Created', `Switching to ${newOrg.name} workspace.`);
    } catch (err: any) {
      toast.error('Creation Failed', err.response?.data?.detail || 'An error occurred.');
    } finally {
      setCreatingOrg(false);
    }
  };

  const handleToggleIntegration = (id: string) => {
    setIntegrations(integrations.map(int => {
      if (int.id === id) {
        const nextActive = !int.active;
        toast.info(
          nextActive ? 'Integration Linked' : 'Integration Severed',
          `The ${int.name} webhook has been ${nextActive ? 'activated' : 'deactivated'}.`
        );
        return { ...int, active: nextActive };
      }
      return int;
    }));
  };

  const handleCreateAPIKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyLabel.trim()) return;
    
    const newKey = {
      id: `key_${Date.now()}`,
      label: newKeyLabel,
      token: `ea_live_val_${Math.random().toString(36).substring(2, 10)}••••••••`,
      created: new Date().toLocaleDateString()
    };
    
    setApiKeys([...apiKeys, newKey]);
    setNewKeyLabel('');
    toast.success('API Token Generated', 'Make sure to save it now. It won\'t be shown again.');
  };

  const handleDeleteAPIKey = (id: string) => {
    setApiKeys(apiKeys.filter(k => k.id !== id));
    toast.success('API Key Revoked', 'The credentials are no longer authorized.');
  };

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      {/* Header */}
      <header>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Settings Console <Settings className="w-6 h-6 text-violet-500" />
        </h1>
        <p className="text-neutral-400 mt-1">Configure tenant profiles, check active pricing tiers, and integrate webhooks.</p>
      </header>

      {/* Tabs Layout Split */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
        
        {/* Navigation Sidebar */}
        <Card className="glass p-3 border-white/5 flex flex-col gap-1">
          {[
            { id: 'org', label: 'Organization & Profile', icon: Building },
            { id: 'billing', label: 'Billing & Subscriptions', icon: CreditCard },
            { id: 'keys', label: 'API Credentials', icon: Key },
            { id: 'integrations', label: 'Connected Apps', icon: Radio },
            { id: 'appearance', label: 'Appearance', icon: Palette },
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer ${
                  activeTab === tab.id 
                    ? 'bg-violet-600/15 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none' 
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </Card>

        {/* Tab Workspaces */}
        <div className="lg:col-span-3">

          {/* ================================================== */}
          {/* TAB: ORGANIZATION & PROFILE */}
          {/* ================================================== */}
          {activeTab === 'org' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Active Tenant Profile</h3>
                  <p className="text-xs text-neutral-400 mt-1">Details of the current operating workspace environment.</p>
                </div>
                
                <div className="flex flex-col gap-4 max-w-md">
                  <Input
                    label="Organization Name"
                    value={editOrgName}
                    onChange={(e) => setEditOrgName(e.target.value)}
                    disabled
                    helperText="Organization names are locked. Create a new organization below to configure a separate tenant workspace."
                  />

                  <Input
                    label="Workspace Slug (Router Key)"
                    value={activeOrg?.slug || ''}
                    disabled
                  />
                </div>
              </Card>

              {/* Create new organization panel */}
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Configure Separate Organization</h3>
                  <p className="text-xs text-neutral-400 mt-1">Spin up an isolated tenant workspace to manage separate campaign goals.</p>
                </div>

                <form onSubmit={handleCreateOrg} className="flex gap-3 max-w-md items-end">
                  <div className="flex-1">
                    <Input
                      label="New Organization Name"
                      placeholder="Acme Global Inc"
                      required
                      value={newOrgName}
                      onChange={(e) => setNewOrgName(e.target.value)}
                    />
                  </div>
                  <Button type="submit" variant="violet" isLoading={creatingOrg} className="h-10 px-5 shrink-0">
                    Create Org
                  </Button>
                </form>
              </Card>
            </div>
          )}

          {/* ================================================== */}
          {/* TAB: BILLING & SUBSCRIPTIONS */}
          {/* ================================================== */}
          {activeTab === 'billing' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Active Plan Tier</h3>
                  <p className="text-xs text-neutral-400 mt-1">Current subscription details and billing cycles.</p>
                </div>

                <div className="flex flex-col md:flex-row justify-between items-start md:items-center p-4 rounded-xl border border-violet-500/20 bg-violet-500/5 gap-4">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-violet-400 font-bold uppercase tracking-wider">Current Subscription Plan</span>
                    <span className="text-xl font-bold text-white mt-1">Enterprise Developer Pro</span>
                    <span className="text-[11px] text-neutral-400 mt-1">Renews on August 15, 2026</span>
                  </div>
                  <div className="flex items-baseline gap-1 text-white">
                    <span className="text-3xl font-extrabold">$249</span>
                    <span className="text-xs text-neutral-400">/ month</span>
                  </div>
                </div>
              </Card>

              {/* Pricing breakdown list */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="p-5 border-white/5 bg-neutral-900/30 flex flex-col justify-between gap-4">
                  <div>
                    <h4 className="font-bold text-sm text-white">Unlimited Agent Tokens</h4>
                    <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                      Run multiple autonomous campaigns side-by-side using Gemini, Claude and GPT gateways without threshold restrictions.
                    </p>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded px-2 py-0.5 self-start">
                    ACTIVE FOR ACTIVE ORGANIZATIONS
                  </span>
                </Card>

                <Card className="p-5 border-white/5 bg-neutral-900/30 flex flex-col justify-between gap-4">
                  <div>
                    <h4 className="font-bold text-sm text-white">Custom SLA Webhooks</h4>
                    <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                      Vectorize bulk databases, store prompt templates versioning, and configure Slack notifications integrations.
                    </p>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded px-2 py-0.5 self-start">
                    ACTIVE FOR ACTIVE ORGANIZATIONS
                  </span>
                </Card>
              </div>
            </div>
          )}

          {/* ================================================== */}
          {/* TAB: API CREDENTIALS */}
          {/* ================================================== */}
          {activeTab === 'keys' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Active API Credentials</h3>
                  <p className="text-xs text-neutral-400 mt-1">Generate developer tokens to authorize external integrations with the EAIMOS API.</p>
                </div>

                {/* API Key list table */}
                <div className="flex flex-col gap-3">
                  {apiKeys.map((key) => (
                    <div key={key.id} className="flex items-center justify-between p-3.5 rounded-lg bg-neutral-950/60 border border-white/5">
                      <div className="flex flex-col">
                        <span className="text-xs font-semibold text-white">{key.label}</span>
                        <span className="font-mono text-[10px] text-violet-400 mt-0.5">{key.token}</span>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] text-neutral-500">Created: {key.created}</span>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => handleDeleteAPIKey(key.id)}
                          className="p-1 h-7 w-7 text-neutral-500 hover:text-rose-400 hover:bg-rose-500/5 rounded-md"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Create key form */}
                <form onSubmit={handleCreateAPIKey} className="flex gap-3 max-w-md items-end border-t border-white/5 pt-4">
                  <div className="flex-1">
                    <Input
                      label="New API Key Label"
                      placeholder="e.g. GitHub Workflow Key"
                      required
                      value={newKeyLabel}
                      onChange={(e) => setNewKeyLabel(e.target.value)}
                    />
                  </div>
                  <Button type="submit" variant="violet" className="h-10 px-5 shrink-0">
                    Generate Key
                  </Button>
                </form>
              </Card>
            </div>
          )}

          {/* ================================================== */}
          {/* TAB: CONNECTED APPS & INTEGRATIONS */}
          {/* ================================================== */}
          {activeTab === 'integrations' && (
            <Card className="glass p-6 border-white/5 flex flex-col gap-6">
              <div>
                <h3 className="font-bold text-base text-white">Connected Applications & Integrations</h3>
                <p className="text-xs text-neutral-400 mt-1">Configure automated triggers and webhook loops across external platforms.</p>
              </div>

              {/* Integrations grid list */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {integrations.map((int) => (
                  <div key={int.id} className="p-4 rounded-xl border border-white/5 bg-neutral-900/30 flex justify-between items-center gap-4 hover:border-violet-500/10 transition-colors">
                    <div>
                      <h4 className="text-sm font-semibold text-white">{int.name}</h4>
                      <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">{int.desc}</p>
                    </div>

                    <button 
                      onClick={() => handleToggleIntegration(int.id)}
                      className="text-neutral-500 hover:text-white transition-colors cursor-pointer"
                    >
                      {int.active ? (
                        <ToggleRight className="w-9 h-9 text-violet-500" />
                      ) : (
                        <ToggleLeft className="w-9 h-9 text-neutral-600" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ================================================== */}
          {/* TAB: APPEARANCE */}
          {/* ================================================== */}
          {activeTab === 'appearance' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Color Theme</h3>
                  <p className="text-xs text-neutral-400 mt-1">
                    Choose between light, dark, or system-synced color scheme. Changes are applied instantly and persisted across sessions.
                  </p>
                </div>

                <div className="flex flex-col gap-4">
                  <ThemeSwitcher variant="tabs" className="self-start" />

                  <div className="grid grid-cols-3 gap-4 mt-2">
                    {[
                      {
                        label: 'Dark',
                        desc: 'Deep dark workspace with violet accents',
                        preview: 'bg-neutral-950 border-white/10',
                        dot: 'bg-violet-500',
                      },
                      {
                        label: 'Light',
                        desc: 'Clean bright surface for daytime productivity',
                        preview: 'bg-white border-neutral-200',
                        dot: 'bg-violet-600',
                      },
                      {
                        label: 'System',
                        desc: 'Automatically follows your OS preference',
                        preview: 'bg-gradient-to-br from-neutral-950 to-white border-neutral-400',
                        dot: 'bg-violet-400',
                      },
                    ].map((item) => (
                      <div key={item.label} className={`p-4 rounded-xl border ${item.preview} flex flex-col gap-2`}>
                        <div className={`w-3 h-3 rounded-full ${item.dot}`} />
                        <p className="text-xs font-bold mt-1 text-neutral-700 dark:text-neutral-200">{item.label}</p>
                        <p className="text-[10px] text-neutral-400 leading-relaxed">{item.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>

              <Card className="glass p-6 border-white/5 flex flex-col gap-4">
                <div>
                  <h3 className="font-bold text-base text-white">Interface Density</h3>
                  <p className="text-xs text-neutral-400 mt-1">Adjust the visual spacing density of the dashboard interface.</p>
                </div>
                <div className="flex gap-3 flex-wrap">
                  {['Compact', 'Default', 'Comfortable'].map((d) => (
                    <button
                      key={d}
                      className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                        d === 'Default'
                          ? 'border-violet-500/30 bg-violet-600/10 text-violet-400'
                          : 'border-white/8 text-neutral-500 hover:text-white hover:border-white/15'
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </Card>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
