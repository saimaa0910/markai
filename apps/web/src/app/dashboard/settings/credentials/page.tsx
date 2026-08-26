'use client';

import * as React from 'react';
import { Card } from '@eaimos/ui';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { Key, Plus, Trash2, Copy, Shield, CheckCircle2, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';

interface APIKeyItem {
  id: string;
  label: string;
  prefix: string;
  masked: string;
  scopes: string[];
  created: string;
  lastUsed: string;
  status: 'active' | 'revoked';
}

export default function APICredentialsPage() {
  const [keys, setKeys] = React.useState<APIKeyItem[]>([
    {
      id: 'key_prod_1',
      label: 'Production Gateway Key',
      prefix: 'ea_live_',
      masked: 'ea_live_••••••••••••••••••••3a9b',
      scopes: ['models:read', 'completions:write', 'embeddings:write'],
      created: '2026-07-01',
      lastUsed: '2026-08-26 11:42 UTC',
      status: 'active',
    },
    {
      id: 'key_dev_2',
      label: 'Staging CI/CD Webhook',
      prefix: 'ea_test_',
      masked: 'ea_test_••••••••••••••••••••8f12',
      scopes: ['agents:run', 'workflows:trigger'],
      created: '2026-08-10',
      lastUsed: '2026-08-25 18:04 UTC',
      status: 'active',
    }
  ]);

  const [newKeyLabel, setNewKeyLabel] = React.useState('');
  const [selectedScopes, setSelectedScopes] = React.useState<string[]>(['models:read', 'completions:write']);
  const [showCreateModal, setShowCreateModal] = React.useState(false);
  const [ipAllowlist, setIpAllowlist] = React.useState('');

  const handleCreateKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyLabel.trim()) return;

    const newKey: APIKeyItem = {
      id: `key_${Date.now()}`,
      label: newKeyLabel,
      prefix: 'ea_live_',
      masked: `ea_live_••••••••••••••••••••${Math.random().toString(36).substring(2, 6)}`,
      scopes: selectedScopes,
      created: new Date().toISOString().split('T')[0],
      lastUsed: 'Never',
      status: 'active',
    };

    setKeys([newKey, ...keys]);
    setNewKeyLabel('');
    setShowCreateModal(false);
    toast.success('API Key Generated', 'Save your credential safely. Tokens are never shown in plaintext again.');
  };

  const handleRevokeKey = (id: string) => {
    setKeys(keys.map(k => k.id === id ? { ...k, status: 'revoked' } : k));
    toast.success('Key Revoked', 'API credential access has been permanently revoked.');
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <div className="space-y-6 max-w-4xl pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            API Credentials <Key className="w-6 h-6 text-violet-500" />
          </h1>
          <p className="text-neutral-400 mt-1">
            Generate and manage scoped API tokens for AI Gateway, Agent Sandbox, and headless automation.
          </p>
        </div>

        <Button
          variant="violet"
          onClick={() => setShowCreateModal(true)}
          className="text-xs self-start sm:self-auto flex items-center gap-2"
        >
          <Plus className="w-3.5 h-3.5" /> Generate New Key
        </Button>
      </div>

      {/* Keys List */}
      <div className="space-y-4">
        {keys.map((k) => (
          <Card key={k.id} className="glass p-5 border-white/5 flex flex-col gap-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-sm text-white">{k.label}</h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                    k.status === 'active' 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}>
                    {k.status}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <code className="bg-neutral-900 border border-white/10 px-2.5 py-1 rounded text-xs font-mono text-violet-300">
                    {k.masked}
                  </code>
                  <button
                    onClick={() => handleCopy(k.masked)}
                    className="p-1 rounded hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
                    title="Copy masked key"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {k.status === 'active' && (
                <Button
                  variant="outline"
                  onClick={() => handleRevokeKey(k.id)}
                  className="text-rose-400 border-rose-500/20 hover:bg-rose-500/10 text-xs"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1" /> Revoke
                </Button>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/5 text-[11px] text-neutral-400">
              <span>Scopes:</span>
              {k.scopes.map(s => (
                <span key={s} className="px-1.5 py-0.5 rounded bg-white/5 text-neutral-300 font-mono">
                  {s}
                </span>
              ))}
              <span className="ml-auto">Created: {k.created}</span>
              <span>• Last used: {k.lastUsed}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* IP Allowlist Card */}
      <Card className="glass p-6 border-white/5 space-y-3">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-violet-400" />
          <h2 className="text-base font-bold text-white">IP Address Allowlist (CIDR)</h2>
        </div>
        <p className="text-xs text-neutral-400">
          Restrict API key requests to designated enterprise IP addresses or subnets.
        </p>
        <div className="flex gap-3 max-w-lg">
          <Input
            placeholder="e.g. 192.0.2.1/32, 198.51.100.0/24"
            value={ipAllowlist}
            onChange={(e) => setIpAllowlist(e.target.value)}
          />
          <Button variant="outline" onClick={() => toast.success('IP Allowlist Updated')} className="text-xs shrink-0">
            Save Allowlist
          </Button>
        </div>
      </Card>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-neutral-900 border border-white/10 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Generate API Credential</h3>
            <p className="text-xs text-neutral-400">Specify an identifier label and permissions for this key.</p>

            <form onSubmit={handleCreateKey} className="space-y-4">
              <Input
                label="Key Label"
                placeholder="e.g. Production Ingestion Service"
                value={newKeyLabel}
                onChange={(e) => setNewKeyLabel(e.target.value)}
                required
              />

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-neutral-300">Scopes</label>
                <div className="space-y-1 text-xs text-neutral-400">
                  {['models:read', 'completions:write', 'embeddings:write', 'agents:run', 'workflows:trigger'].map(scope => (
                    <label key={scope} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedScopes.includes(scope)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedScopes([...selectedScopes, scope]);
                          else setSelectedScopes(selectedScopes.filter(s => s !== scope));
                        }}
                        className="rounded border-white/20 bg-neutral-950 text-violet-600"
                      />
                      <span className="font-mono text-[11px]">{scope}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)} className="flex-1 text-xs">
                  Cancel
                </Button>
                <Button type="submit" variant="violet" className="flex-1 text-xs">
                  Create Key
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
