'use client';

import * as React from 'react';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';
import {
  Plug, CheckCircle2, XCircle, RefreshCw, ExternalLink,
  Webhook, Zap, Database, Mail, MessageSquare, Calendar, CreditCard
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// Integration definitions
// ─────────────────────────────────────────────────────────────────────────────
export interface IntegrationDef {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ReactNode;
  status: 'connected' | 'disconnected' | 'coming_soon';
  lastSync?: string;
  features: string[];
  color: string;
}

const INTEGRATIONS: IntegrationDef[] = [
  {
    id: 'slack',
    name: 'Slack',
    description: 'Receive campaign alerts, AI generation notifications, and CRM updates in Slack channels.',
    category: 'Notifications',
    icon: <MessageSquare className="w-5 h-5" />,
    status: 'disconnected',
    features: ['Channel alerts', 'Lead notifications', 'AI insights'],
    color: 'from-[#4A154B] to-[#611f69]',
  },
  {
    id: 'sendgrid',
    name: 'SendGrid',
    description: 'Send transactional and marketing emails powered by AI-generated copy directly via SendGrid.',
    category: 'Email',
    icon: <Mail className="w-5 h-5" />,
    status: 'disconnected',
    features: ['Email delivery', 'Template sync', 'Analytics'],
    color: 'from-[#1a82e2] to-[#0a6bc2]',
  },
  {
    id: 'webhooks',
    name: 'Webhooks',
    description: 'Send real-time event payloads to any HTTP endpoint when CRM or AI events fire.',
    category: 'Developer',
    icon: <Webhook className="w-5 h-5" />,
    status: 'disconnected',
    features: ['Event-driven', 'Custom endpoints', 'Retry logic'],
    color: 'from-violet-700 to-indigo-700',
  },
  {
    id: 'zapier',
    name: 'Zapier',
    description: 'Connect EAIMOS to 6,000+ apps with no-code Zaps triggered by your CRM and AI events.',
    category: 'Automation',
    icon: <Zap className="w-5 h-5" />,
    status: 'coming_soon',
    features: ['5000+ apps', 'No-code', 'Two-way sync'],
    color: 'from-[#FF4F00] to-[#CC3F00]',
  },
  {
    id: 'postgres',
    name: 'External PostgreSQL',
    description: 'Export your CRM contacts, leads, and AI generation records to an external Postgres database.',
    category: 'Data Export',
    icon: <Database className="w-5 h-5" />,
    status: 'coming_soon',
    features: ['Scheduled export', 'Real-time sync', 'Schema mapping'],
    color: 'from-[#336791] to-[#1a4a6e]',
  },
  {
    id: 'google-cal',
    name: 'Google Calendar',
    description: 'Sync CRM lead activities and campaign schedules to Google Calendar automatically.',
    category: 'Productivity',
    icon: <Calendar className="w-5 h-5" />,
    status: 'coming_soon',
    features: ['Activity sync', 'Meeting scheduling', 'Reminders'],
    color: 'from-[#1967D2] to-[#0f4a9c]',
  },
  {
    id: 'stripe',
    name: 'Stripe',
    description: 'Attribute revenue from won CRM deals to Stripe payments for closed-loop analytics.',
    category: 'Revenue',
    icon: <CreditCard className="w-5 h-5" />,
    status: 'coming_soon',
    features: ['Revenue attribution', 'Deal correlation', 'MRR tracking'],
    color: 'from-[#635BFF] to-[#4F46D4]',
  },
];

const CATEGORIES = ['All', ...new Set(INTEGRATIONS.map((i) => i.category))];

// ─────────────────────────────────────────────────────────────────────────────
// Integration Card
// ─────────────────────────────────────────────────────────────────────────────
function IntegrationCard({ integration, delay }: { integration: IntegrationDef; delay: number }) {
  const [connecting, setConnecting] = React.useState(false);
  const isConnected  = integration.status === 'connected';
  const isComingSoon = integration.status === 'coming_soon';

  const handleConnect = async () => {
    if (isComingSoon) {
      toast.success('Noted!', `${integration.name} integration is coming soon. You'll be notified on launch.`);
      return;
    }
    setConnecting(true);
    await new Promise((r) => setTimeout(r, 1200));
    setConnecting(false);
    toast.success('OAuth Initiated', `Redirecting to ${integration.name} authorization...`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="rounded-xl border border-white/5 bg-neutral-950/40 p-5 flex flex-col gap-4 hover:border-violet-500/20 transition-all group"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl bg-gradient-to-br ${integration.color} text-white shrink-0`}>
            {integration.icon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm text-white">{integration.name}</h3>
              {isComingSoon && <Badge variant="amber" size="sm">Soon</Badge>}
            </div>
            <Badge variant="neutral" size="sm" className="mt-0.5">{integration.category}</Badge>
          </div>
        </div>
        {isConnected
          ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          : !isComingSoon && <XCircle className="w-4 h-4 text-neutral-600 shrink-0" />
        }
      </div>

      {/* Description */}
      <p className="text-[12px] text-neutral-400 leading-relaxed">{integration.description}</p>

      {/* Features */}
      <div className="flex flex-wrap gap-1.5">
        {integration.features.map((f) => (
          <Badge key={f} variant="neutral" size="sm">{f}</Badge>
        ))}
      </div>

      {/* Action row */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        {integration.lastSync ? (
          <div className="flex items-center gap-1 text-[10px] text-neutral-500">
            <RefreshCw className="w-3 h-3" />
            Synced {integration.lastSync}
          </div>
        ) : (
          <Badge variant={isConnected ? 'emerald' : isComingSoon ? 'amber' : 'neutral'} dot>
            {isConnected ? 'Connected' : isComingSoon ? 'Coming Soon' : 'Not Connected'}
          </Badge>
        )}

        <Button
          variant={isConnected ? 'outline' : isComingSoon ? 'ghost' : 'violet'}
          size="sm"
          onClick={handleConnect}
          isLoading={connecting}
          className="h-7 text-[11px]"
        >
          {isConnected ? (
            <><RefreshCw className="w-3 h-3" /> Reconnect</>
          ) : isComingSoon ? (
            'Notify Me'
          ) : (
            <><ExternalLink className="w-3 h-3" /> Connect</>
          )}
        </Button>
      </div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Integrations Page Component
// ─────────────────────────────────────────────────────────────────────────────
export function IntegrationsPage() {
  const [activeCategory, setActiveCategory] = React.useState('All');

  const filtered = activeCategory === 'All'
    ? INTEGRATIONS
    : INTEGRATIONS.filter((i) => i.category === activeCategory);

  const connectedCount = INTEGRATIONS.filter((i) => i.status === 'connected').length;

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Integrations & Connectors"
        description="Connect EAIMOS to your existing toolstack. OAuth flows, webhook endpoints, and data sync."
        icon={<Plug className="w-5 h-5" />}
        badge={<Badge variant={connectedCount > 0 ? 'emerald' : 'neutral'}>{connectedCount} Connected</Badge>}
      />

      {/* Category filter */}
      <div className="flex items-center gap-2 flex-wrap">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`text-xs px-3 py-1.5 rounded-full border font-semibold transition-all cursor-pointer ${
              activeCategory === cat
                ? 'border-violet-500 bg-violet-500/10 text-violet-400'
                : 'border-white/10 text-neutral-400 hover:text-white hover:border-white/20'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Integration grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {filtered.map((integration, idx) => (
          <IntegrationCard key={integration.id} integration={integration} delay={idx * 0.05} />
        ))}
      </div>

      {/* Webhook endpoint info */}
      <div className="p-5 rounded-xl border border-violet-500/15 bg-violet-500/5 flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Webhook className="w-4 h-4 text-violet-400" />
          <h3 className="text-sm font-bold text-white">Inbound Webhook Endpoint</h3>
        </div>
        <p className="text-[12px] text-neutral-400">
          Send events from any platform to EAIMOS using your organization's webhook endpoint:
        </p>
        <code className="text-xs font-mono text-violet-300 bg-neutral-900 border border-white/5 px-3 py-2 rounded-lg">
          POST https://api.eaimos.com/api/v1/webhooks/inbound/{'{'}org_id{'}'}
        </code>
      </div>
    </div>
  );
}

export default IntegrationsPage;
