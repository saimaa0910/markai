'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { 
  Webhook, ShieldAlert, RefreshCw, ArrowRight, Sparkles, CheckCircle2, ChevronRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { CodeBlock } from '@/components/ui/code-block';
import { useRouter } from 'next/navigation';

interface WebhookEvent {
  name: string;
  desc: string;
  payload: string;
}

const EVENTS: WebhookEvent[] = [
  {
    name: 'lead.enriched',
    desc: 'Triggered when an inbound sales contact is resolved, scraped, and corporate stats are mapped.',
    payload: `{\n  "id": "evt_9a2f1c84",\n  "type": "lead.enriched",\n  "created_at": "2026-07-14T21:38:30Z",\n  "data": {\n    "lead_email": "john@acme.com",\n    "company_name": "Acme Corp",\n    "company_size": "120",\n    "enrichment_status": "success"\n  }\n}`,
  },
  {
    name: 'campaign.completed',
    desc: 'Triggered when an autonomous multi-channel campaign publishes all drafts and schedules.',
    payload: `{\n  "id": "evt_0f28ca91",\n  "type": "campaign.completed",\n  "created_at": "2026-07-14T21:40:00Z",\n  "data": {\n    "campaign_id": "camp_8b2e10fc",\n    "channels": ["linkedin", "google-ads"],\n    "total_variants": 6,\n    "status": "published"\n  }\n}`,
  },
  {
    name: 'agent.errored',
    desc: 'Triggered when an active AI agent encounters a model rate limit or fails brand schema validation.',
    payload: `{\n  "id": "evt_ff39ac12",\n  "type": "agent.errored",\n  "created_at": "2026-07-14T21:42:15Z",\n  "data": {\n    "agent_id": "agent_8f2e91a0",\n    "error_code": "brand_schema_violation",\n    "message": "Generated copy contains blocked competitor mentions."\n  }\n}`,
  },
];

const RETRIES = [
  { attempt: '1st', delay: 'Immediate', desc: 'Attempted instantly upon event dispatch trigger.' },
  { attempt: '2nd', delay: '5 minutes', desc: 'Attempted if first endpoint response code is not 2xx.' },
  { attempt: '3rd', delay: '15 minutes', desc: 'Retry queue buffer runs with linear exponential backoff.' },
  { attempt: '4th', delay: '1 hour', desc: 'Audit system logs failure state and schedules sync.' },
  { attempt: '5th', delay: '6 hours', desc: 'Final retry. If failed again, event status is marked failed.' },
];

const SIGN_CODE = `const crypto = require('crypto');\n\nfunction verifyWebhook(payload, signature, secret) {\n  const hmac = crypto.createHmac('sha256', secret);\n  const digest = hmac.update(payload).digest('hex');\n  \n  return signature === \`t=\${digest}\`;\n}\n\n// Usage:\n// const isValid = verifyWebhook(\n//   req.body,\n//   req.headers['viptant-signature'],\n//   process.env.VIPTANT_WEBHOOK_SECRET\n// );`;

export default function WebhooksPage() {
  const router = useRouter();
  const [selectedEvent, setSelectedEvent] = React.useState<WebhookEvent>(EVENTS[0]);

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Webhooks Portal</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Real-Time Event Webhooks
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Sync database events instantly. Register endpoint URLs to receive JSON webhook notifications when leads enrich, posts publish, or agents errored.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Split Section: Verification & Events Catalog ───────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-8 text-left">
        
        {/* Verification and signing details (col-span-6) */}
        <div className="lg:col-span-6 space-y-8">
          <FadeUp>
            <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-3">
              <ShieldAlert className="w-5 h-5 text-violet-400" /> Signature Verification
            </h3>
            <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed mb-4">
              Viptant signs all outgoing webhook payloads with a cryptographical signature. Always verify incoming webhook requests before ingestion to prevent endpoint spoofing:
            </p>
            <p className="text-xs text-neutral-500 leading-relaxed mb-6">
              Each POST request contains a header: <code className="text-violet-400 font-mono text-[10px]">viptant-signature</code>. It includes a SHA-256 HMAC generated using your endpoint signing secret.
            </p>
            <CodeBlock code={SIGN_CODE} language="javascript" copyable maxHeight="300px" />
          </FadeUp>
        </div>

        {/* Dynamic Events Catalog (col-span-6) */}
        <div className="lg:col-span-6 space-y-6">
          <FadeUp>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Webhook className="w-5 h-5 text-indigo-400" /> Event Dictionary
            </h3>
            <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed mb-6">
              Select an event type below to inspect sample payload data structures dispatched to your destination endpoint.
            </p>
          </FadeUp>

          {/* Event selection list */}
          <div className="flex gap-2 mb-4 overflow-x-auto pb-1 scrollbar-none">
            {EVENTS.map((evt) => (
              <button
                key={evt.name}
                onClick={() => setSelectedEvent(evt)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors cursor-pointer shrink-0 border ${
                  selectedEvent.name === evt.name
                    ? 'bg-violet-600 border-violet-500 text-white font-bold'
                    : 'bg-neutral-900 border-white/5 text-neutral-400 hover:text-white'
                }`}
              >
                {evt.name}
              </button>
            ))}
          </div>

          <FadeUp>
            <div className="p-4 rounded-xl border border-white/6 bg-neutral-950/40 mb-4">
              <span className="text-[10px] text-neutral-500 font-mono block mb-1">EVENT DESCRIPTION</span>
              <p className="text-xs text-neutral-300 leading-relaxed">{selectedEvent.desc}</p>
            </div>
            <CodeBlock code={selectedEvent.payload} language="json" copyable maxHeight="280px" />
          </FadeUp>
        </div>
      </section>

      {/* ─── Webhooks Retry Timeline Section ────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Reliable Delivery</SectionLabel>
              <GradientHeading className="text-3xl font-extrabold tracking-tight mt-2 mb-3">
                Webhook Delivery Retries
              </GradientHeading>
              <p className="text-neutral-400 text-xs sm:text-sm max-w-md mx-auto">
                Our delivery queue automatically schedules retries when endpoints respond with 5xx timeouts, using exponential backoff schedules.
              </p>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            {RETRIES.map((ret, idx) => (
              <FadeUp 
                key={ret.attempt} 
                delay={idx * 0.05} 
                className="p-5 rounded-lg border border-white/5 bg-black hover:border-violet-500/20 transition-all text-left"
              >
                <div className="flex justify-between items-center mb-3">
                  <span className="text-[9px] font-bold text-violet-400 uppercase tracking-wider">{ret.attempt} attempt</span>
                  <span className="px-2 py-0.5 rounded bg-violet-600/10 text-[8px] font-mono text-violet-300 font-semibold">{ret.delay}</span>
                </div>
                <p className="text-[10px] text-neutral-400 leading-relaxed">{ret.desc}</p>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Bottom CTA banner ──────────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50 text-center relative overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-violet-600/5 blur-[120px] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <FadeUp>
            <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-4">
              Connect Webhooks in Sandbox
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Navigate to Viptant dashboard settings to input webhook endpoint URLs and begin testing event notifications.
            </p>
            <div className="flex justify-center gap-3">
              <Button 
                variant="violet" 
                size="lg"
                onClick={() => router.push('/developers/api-docs')}
                className="h-11 px-6 text-xs font-semibold"
              >
                Inspect API Specs <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}
