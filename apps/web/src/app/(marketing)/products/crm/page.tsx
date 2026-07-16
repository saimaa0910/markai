'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users, Building2, UserSquare, CalendarDays, Compass, 
  ArrowRight, Search, Zap, Check, CheckCircle2, ChevronRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function CRMPage() {
  const router = useRouter();

  // State for CRM enrichment mockup simulator
  const [enriched, setEnriched] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const simulateEnrichment = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setEnriched(true);
    }, 1200);
  };

  const pillars = [
    { icon: Users, name: 'Lead Enrichment', desc: 'Autonomous agents scan web data, news articles, and LinkedIn to enrich email contacts into deep company profiles.' },
    { icon: Building2, name: 'Company Intelligence', desc: 'Maintain complete data profiles on companies—including funding history, active tech stacks, and team counts.' },
    { icon: UserSquare, name: 'Contact Sync', desc: 'Track key personnel, job title changes, and organizational shifts automatically without manual CRM logs.' },
    { icon: CalendarDays, name: 'Activity Logging', desc: 'Synchronize inbound emails, calendar syncs, meeting transcript takeaways, and channel clicks in one record.' },
    { icon: Compass, name: 'Routing & Assignment', desc: 'Assign hot leads to appropriate sales reps or trigger automated AI response chains instantly.' },
  ];

  const features = [
    { title: 'Zero Manual Entry', desc: 'Agents populate fields, titles, sizes, and activities automatically based on web scraping and integrations.' },
    { title: 'Semantic Deduplication', desc: 'Identify duplicates based on intent, spelling variations, and company ownership mapping.' },
    { title: 'Automatic Outbox Sync', desc: 'Send personalized emails and record the outcome directly back into lead records.' },
    { title: 'Predictive Lead Scoring', desc: 'Rank leads by fit based on historic conversion datasets and token intent analytics.' },
    { title: 'GDPR Opt-Out Automation', desc: 'Automatically tag and restrict outreach to leads who request data removal.' },
    { title: 'Custom Field Injections', desc: 'Define proprietary data schemas and let agents map web scraping outputs directly to them.' },
  ];

  const comparisons = [
    { metric: 'Data Entry', viptant: '100% automated by agents', wrapper: 'Manual typing by sales reps' },
    { metric: 'Enrichment Frequency', viptant: 'Real-time web monitoring', wrapper: 'Lagging monthly batches' },
    { metric: 'Integration Sync', viptant: 'Native vector & model mappings', wrapper: 'Complex third-party APIs' },
    { metric: 'Lead Routing', viptant: 'Immediate semantic triggers', wrapper: 'Static conditional routes' },
    { metric: 'Data Freshness', viptant: 'Updates on title shift triggers', wrapper: 'Becomes stale within 90 days' },
  ];

  const faqs = [
    { q: 'How does lead enrichment work?', a: 'When a lead submits an email, Viptant agents search public databases, LinkedIn profiles, and news releases to extract information like company size, tech stack, funding, and recent achievements.' },
    { q: 'Does it sync with HubSpot or Salesforce?', a: 'Yes. Viptant integrates bi-directionally with HubSpot, Salesforce, and Pipedrive. You can enrich leads in Viptant and push them back to your legacy CRM.' },
    { q: 'Is this compliant with privacy laws?', a: 'Yes. Viptant only collects public data and complies fully with GDPR, CCPA, and CAN-SPAM regulations. Opt-out requests are processed globally across databases instantly.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 overflow-hidden bg-grid-dots">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 text-left">
            <FadeUp>
              <SectionLabel>Sales Intelligence</SectionLabel>
              <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 leading-tight">
                The First CRM That Updates Itself
              </GradientHeading>
              <p className="text-neutral-400 text-sm sm:text-base leading-relaxed max-w-xl mb-8">
                Stop typing data. Let autonomous marketing agents enrich contacts, score sales leads, log meeting details, and manage pipelines 24/7.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center gap-3">
                <Button 
                  variant="violet" 
                  size="lg"
                  onClick={() => router.push('/auth/register')}
                  className="w-full sm:w-auto h-11 px-6 text-xs font-semibold"
                >
                  Start Free Trial <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
                <Button 
                  variant="outline" 
                  size="lg"
                  onClick={() => router.push('/company/contact')}
                  className="w-full sm:w-auto h-11 px-6 text-xs text-neutral-300 hover:text-white"
                >
                  Book Integrations Call
                </Button>
              </div>
            </FadeUp>
          </div>

          {/* CRM Enrichment Mockup */}
          <div className="lg:col-span-5">
            <FadeUp delay={0.2} className="relative rounded-2xl border border-white/10 bg-neutral-950/80 p-5 glass overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3.5 mb-5">
                <span className="text-xs font-semibold text-neutral-300 flex items-center gap-1.5">
                  <Users className="w-4 h-4 text-violet-400" /> Lead Pipeline
                </span>
                <span className="px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-[9px] text-violet-400 font-mono">ENRICHMENT</span>
              </div>

              {/* Lead Card Visual */}
              <div className="p-4 rounded-xl bg-neutral-900 border border-white/5 mb-5 space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-xs font-bold text-white">john@acme.com</h4>
                    <p className="text-[10px] text-neutral-500">Inbound Lead — 4m ago</p>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-[8px] font-bold text-amber-400">UNRESOLVED</span>
                </div>

                <div className="border-t border-white/5 pt-3 space-y-1.5 text-[9px] font-mono">
                  {enriched ? (
                    <>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Name:</span>
                        <span className="text-white">John Smith</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Company:</span>
                        <span className="text-violet-400 font-bold">Acme Corp</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Employees:</span>
                        <span className="text-white">124 (Mid-Market)</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Funding:</span>
                        <span className="text-white">$14M Series B</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Tech Stack:</span>
                        <span className="text-white">Next.js, Salesforce, G-Suite</span>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-4 text-neutral-600">
                      Empty Lead Profile. Click Enrich to resolve company data.
                    </div>
                  )}
                </div>
              </div>

              {/* Trigger Button */}
              <Button
                variant={enriched ? "outline" : "violet"}
                onClick={simulateEnrichment}
                className="w-full h-9 text-[10px] gap-2"
                isLoading={loading}
                disabled={enriched}
              >
                {enriched ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" /> Profile Enriched
                  </>
                ) : (
                  <>
                    <Search className="w-3.5 h-3.5" /> Enrich Lead via AI Agents
                  </>
                )}
              </Button>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* ─── Platform Pillars Section ───────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <FadeUp>
              <SectionLabel>CRM Capabilities</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Five Engines of Agentic CRM
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            {pillars.map((p, i) => {
              const Icon = p.icon;
              return (
                <FadeUp 
                  key={p.name} 
                  delay={i * 0.05} 
                  className="p-6 rounded-xl border border-white/6 bg-neutral-900/10 hover:border-violet-500/20 hover:bg-neutral-900/30 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="w-9 h-9 rounded-lg bg-neutral-950 border border-white/8 flex items-center justify-center text-neutral-400 mb-4">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h4 className="text-sm font-bold text-white mb-2">{p.name}</h4>
                    <p className="text-neutral-500 text-[11px] sm:text-xs leading-relaxed">{p.desc}</p>
                  </div>
                </FadeUp>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── Features Grid Section ──────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <FadeUp>
              <SectionLabel>Features</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Autonomous Database Management
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((f, i) => (
              <FadeUp 
                key={f.title} 
                delay={i * 0.04} 
                className="p-8 rounded-xl border border-white/6 bg-neutral-950/20 hover:border-violet-500/20 hover:bg-neutral-900/10 transition-all duration-300 group text-left"
              >
                <h4 className="text-base font-bold text-white mb-2 group-hover:text-violet-300 transition-colors">{f.title}</h4>
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed">{f.desc}</p>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Comparison Section ────────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Performance Comparison</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                How Viptant Compares to Legacy CRMs
              </GradientHeading>
            </FadeUp>
          </div>

          <FadeUp delay={0.1} className="rounded-xl border border-white/6 overflow-hidden bg-black shadow-xl">
            <div className="grid grid-cols-3 p-4 bg-neutral-900/50 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-neutral-400 border-b border-white/5">
              <span>Feature</span>
              <span>Viptant CRM</span>
              <span>Legacy CRMs</span>
            </div>

            {comparisons.map((c) => (
              <div key={c.metric} className="grid grid-cols-3 p-4 text-xs text-neutral-300 border-b border-white/5 last:border-0 hover:bg-white/2">
                <span className="font-semibold text-white">{c.metric}</span>
                <span className="text-violet-400 font-medium">{c.viptant}</span>
                <span className="text-neutral-500">{c.wrapper}</span>
              </div>
            ))}
          </FadeUp>
        </div>
      </section>

      {/* ─── Product Specific FAQs Section ─────────────────────────────────── */}
      <section className="py-24 border-t border-white/5">
        <div className="max-w-3xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>CRM FAQ</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Common CRM Questions
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="border-t border-white/5">
            {faqs.map((faq, idx) => (
              <FaqItem key={faq.q} q={faq.q} a={faq.a} index={idx} />
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
              Get Started with the Agentic CRM
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Enable your sales teams. Build clean records and trigger conversion routes using autonomous research.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Button 
                variant="violet" 
                size="lg"
                onClick={() => router.push('/auth/register')}
                className="w-full sm:w-auto h-11 px-6 text-xs font-semibold"
              >
                Start Free Trial <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
              <Button 
                variant="outline" 
                size="lg"
                onClick={() => router.push('/company/contact')}
                className="w-full sm:w-auto h-11 px-6 text-xs text-neutral-300 hover:text-white"
              >
                Talk to CRM Architect
              </Button>
            </div>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}

// Reusable micro-FAQ item
function FaqItem({ q, a, index }: { q: string; a: string; index: number }) {
  const [open, setOpen] = React.useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35, delay: index * 0.04 }}
      className="border-b border-white/6 py-5"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-left cursor-pointer group"
      >
        <span className="text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">
          {q}
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          className="text-neutral-500 text-xs"
        >
          ▼
        </motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <p className="pt-3.5 text-xs sm:text-sm text-neutral-400 leading-relaxed max-w-2xl">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
