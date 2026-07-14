import * as React from 'react';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { 
  Shield, Users, Key, Sliders, FileText, Plus, 
  RotateCw, Save, DollarSign, RefreshCw, CheckCircle2 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';

interface OrgCap {
  id: string;
  name: string;
  creditLimit: number;
  creditUsed: number;
  rpmLimit: number;
  tpmLimit: number;
}

interface AuditLog {
  id: string;
  actor: string;
  action: string;
  target: string;
  timestamp: string;
}

const MOCK_ORGS: OrgCap[] = [
  { id: 'org-1', name: 'Saimaa0910 Corp', creditLimit: 5000, creditUsed: 1250, rpmLimit: 1000, tpmLimit: 150000 },
  { id: 'org-2', name: 'Viptant Marketing', creditLimit: 2500, creditUsed: 840, rpmLimit: 500, tpmLimit: 80000 },
  { id: 'org-3', name: 'Acme Growth Inc', creditLimit: 1000, creditUsed: 980, rpmLimit: 200, tpmLimit: 30000 },
];

const MOCK_AUDITS: AuditLog[] = [
  { id: 'aud-1', actor: 'admin@viptant.com', action: 'ROTATE_API_KEY', target: 'openai_key_s4', timestamp: '2026-07-14T09:40:00Z' },
  { id: 'aud-2', actor: 'admin@viptant.com', action: 'CREDITS_ADD', target: 'org-1 (+$500)', timestamp: '2026-07-14T08:12:00Z' },
  { id: 'aud-3', actor: 'system@viptant.com', action: 'RATE_LIMIT_BLOCK', target: 'org-3 (RPM Exceeded)', timestamp: '2026-07-14T07:55:00Z' },
];

export function AdminPage() {
  const [activeTab, setActiveTab] = React.useState<'orgs' | 'keys' | 'limits' | 'audits'>('orgs');
  const [orgs, setOrgs] = React.useState<OrgCap[]>(MOCK_ORGS);
  const [audits, setAudits] = React.useState<AuditLog[]>(MOCK_AUDITS);
  
  // Credit update inputs
  const [amountToAdd, setAmountToAdd] = React.useState<Record<string, string>>({});
  
  // Rate limits inputs
  const [rpmInput, setRpmInput] = React.useState<Record<string, number>>({
    'org-1': 1000,
    'org-2': 500,
    'org-3': 200,
  });

  const handleAddCredits = (orgId: string) => {
    const amount = Number(amountToAdd[orgId]);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Invalid Amount', 'Enter a positive numeric balance.');
      return;
    }

    setOrgs(
      orgs.map((org) =>
        org.id === orgId ? { ...org, creditLimit: org.creditLimit + amount } : org
      )
    );
    
    // Add to audit trail
    const newAudit: AuditLog = {
      id: `aud-${Date.now()}`,
      actor: 'admin@viptant.com',
      action: 'CREDITS_ADD',
      target: `${orgs.find(o => o.id === orgId)?.name} (+$${amount})`,
      timestamp: new Date().toISOString(),
    };
    setAudits([newAudit, ...audits]);
    setAmountToAdd((prev) => ({ ...prev, [orgId]: '' }));
    toast.success('Credits Added', `Injected $${amount} to organization limits.`);
  };

  const handleRotateKey = (keyName: string) => {
    toast.success('Key Rotated', `${keyName} credential secret rotated successfully.`);
    const newAudit: AuditLog = {
      id: `aud-${Date.now()}`,
      actor: 'admin@viptant.com',
      action: 'ROTATE_API_KEY',
      target: keyName,
      timestamp: new Date().toISOString(),
    };
    setAudits([newAudit, ...audits]);
  };

  const handleSaveRateLimits = (orgId: string) => {
    const nextRpm = rpmInput[orgId];
    setOrgs(
      orgs.map((org) => (org.id === orgId ? { ...org, rpmLimit: nextRpm } : org))
    );
    toast.success('Rate Limits Applied', 'Modified organization rate parameters.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="AI Admin Console"
        description="Global tenant administration, rate limit controls, credits allocations, credential rotation, and system auditing."
        icon={<Shield className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">System admin</Badge>}
      />

      {/* Admin sections navigation layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Navigation panel */}
        <div className="flex flex-col gap-2">
          {[
            { id: 'orgs', label: 'Organizations & Credits', icon: <Users className="w-4 h-4" /> },
            { id: 'limits', label: 'Rate limits configuration', icon: <Sliders className="w-4 h-4" /> },
            { id: 'keys', label: 'Provider API Keys', icon: <Key className="w-4 h-4" /> },
            { id: 'audits', label: 'System audit logs', icon: <FileText className="w-4 h-4" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-semibold text-left transition-all ${
                activeTab === tab.id
                  ? 'bg-violet-600 border-violet-500/30 text-white shadow-lg'
                  : 'bg-neutral-950/20 border-white/5 text-neutral-400 hover:text-white'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Console Panels */}
        <div className="lg:col-span-3">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === 'orgs' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">Tenant organizations credits</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Control token expenditures and inject credit balances.</p>
                  </div>

                  <div className="flex flex-col divide-y divide-white/5 mt-2">
                    {orgs.map((org) => {
                      const usedPercent = Math.min(100, Math.round((org.creditUsed / org.creditLimit) * 100));
                      return (
                        <div key={org.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 first:pt-0 last:pb-0">
                          <div className="flex-1 flex flex-col gap-2">
                            <span className="text-xs font-bold text-white">{org.name}</span>
                            
                            <div className="flex items-center gap-4 text-[10px] text-neutral-400">
                              <span>Credits: <b>${org.creditUsed} / ${org.creditLimit}</b> used ({usedPercent}%)</span>
                            </div>

                            <div className="w-full max-w-md h-1.5 rounded-full bg-neutral-900 border border-white/5 overflow-hidden">
                              <div className="h-full bg-violet-600 rounded-full" style={{ width: `${usedPercent}%` }} />
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <Input
                              type="number"
                              placeholder="Amount ($)"
                              value={amountToAdd[org.id] || ''}
                              onChange={(e) => setAmountToAdd({ ...amountToAdd, [org.id]: e.target.value })}
                              className="bg-neutral-950/40 border-white/5 h-8 w-24 text-[11px]"
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleAddCredits(org.id)}
                              className="h-8 text-[10px] border-white/5 bg-neutral-900 hover:bg-neutral-800"
                            >
                              <Plus className="w-3.5 h-3.5 mr-1" />
                              Add Credits
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {activeTab === 'limits' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">RPM Rate limit modifiers</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Tweak active requests-per-minute constraints on organizations.</p>
                  </div>

                  <div className="flex flex-col divide-y divide-white/5 mt-2">
                    {orgs.map((org) => (
                      <div key={org.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 first:pt-0 last:pb-0">
                        <div className="flex flex-col gap-1">
                          <span className="text-xs font-bold text-white">{org.name}</span>
                          <span className="text-[10px] text-neutral-500 font-mono">Current RPM Limit: {org.rpmLimit}</span>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <Input
                            type="number"
                            value={rpmInput[org.id] || 0}
                            onChange={(e) => setRpmInput({ ...rpmInput, [org.id]: Number(e.target.value) })}
                            className="bg-neutral-950/40 border-white/5 h-8 w-24 text-[11px] font-mono"
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSaveRateLimits(org.id)}
                            className="h-8 text-[10px] border-white/5 bg-neutral-900 hover:bg-neutral-800"
                          >
                            <Save className="w-3.5 h-3.5 mr-1" />
                            Apply
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {activeTab === 'keys' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">Credential Rotation Console</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Manage and rotate token authorization key parameters.</p>
                  </div>

                  <div className="flex flex-col gap-3 mt-2">
                    {[
                      { key: 'groq_key', label: 'Groq Auth Token', masked: 'groq_sec_sk_*****_t9fd' },
                      { key: 'openai_key', label: 'OpenAI Secret Key', masked: 'sk-proj-*****_y4a2' },
                      { key: 'google_key', label: 'Google Studio Key', masked: 'ai_studio_api_*****_23m1' },
                    ].map((row) => (
                      <div key={row.key} className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between gap-4 text-xs font-mono">
                        <div className="flex flex-col gap-1">
                          <span className="font-sans font-bold text-white">{row.label}</span>
                          <span className="text-neutral-500 text-[10px]">{row.masked}</span>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRotateKey(row.label)}
                          className="h-7 text-[9px] border-white/5 bg-neutral-900 hover:bg-neutral-800"
                        >
                          <RotateCw className="w-3 h-3 mr-1" />
                          Rotate Key
                        </Button>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {activeTab === 'audits' && (
                <Card className="flex flex-col gap-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">System audit log trail</h3>
                    <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Logs recording system changes, rotated credentials, and limit modifications.</p>
                  </div>

                  <div className="flex flex-col gap-2.5 mt-2">
                    {audits.map((item) => (
                      <div key={item.id} className="p-3 rounded-lg border border-white/5 bg-neutral-950/20 flex flex-col md:flex-row md:items-center justify-between gap-3 text-[11px] font-mono leading-relaxed">
                        <div className="flex flex-col gap-0.5">
                          <div className="flex items-center gap-1.5">
                            <span className="text-violet-400 font-bold">{item.action}</span>
                            <span className="text-neutral-500">by {item.actor}</span>
                          </div>
                          <span className="text-neutral-300">Target: {item.target}</span>
                        </div>
                        <span className="text-neutral-500 text-[10px] shrink-0">
                          {new Date(item.timestamp).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
