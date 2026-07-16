'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3, TrendingUp, Compass, Activity, BrainCircuit, 
  ArrowRight, Sparkles, RefreshCw, CheckCircle2, ChevronRight, Check 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function AnalyticsPage() {
  const router = useRouter();

  // State for interactive forecast simulation
  const [projected, setProjected] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const simulateForecasting = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setProjected(true);
    }, 1200);
  };

  const pillars = [
    { icon: BarChart3, name: 'Unified Dashboards', desc: 'Aggregate data from Google Analytics, Stripe, HubSpot, and ad channels into one centralized visual interface.' },
    { icon: TrendingUp, name: 'Multi-Touch Attribution', desc: 'Accurately attribute conversion values to the specific creative variations and channels that influenced buying paths.' },
    { icon: Compass, name: 'Predictive Forecasting', desc: 'Predict future pipeline growth and budget optimization using historic performance regression models.' },
    { icon: BrainCircuit, name: 'AI Diagnostic Insights', desc: 'Receive automated notifications when cost metrics drift, detailing exactly what copy or audience group is causing the anomaly.' },
    { icon: Activity, name: 'Real-Time Telemetry', desc: 'Access metrics immediately upon trigger actions rather than waiting 24 to 48 hours for third-party dashboard updates.' },
  ];

  const features = [
    { title: 'Custom Attribution Models', desc: 'Configure First-Touch, Last-Touch, or Linear attribution rules to fit your sales lifecycle.' },
    { title: 'Token Diagnostic Logs', desc: 'Track token efficiency, model costs, and prompt performance across your active AI agents.' },
    { title: 'Cohort Retention Funnels', desc: 'Analyze sign-up cohorts to measure lifetime value (LTV) and long-term user retention.' },
    { title: 'Semantic Event Tracking', desc: 'Log website events based on intent rather than static CSS class selectors.' },
    { title: 'Auto-Reporting Digests', desc: 'Send daily Slack summaries or custom formatted PDF reports to stakeholders automatically.' },
    { title: 'Threshold Alerts', desc: 'Trigger alerts immediately when campaign CPCs cross specified boundaries.' },
  ];

  const comparisons = [
    { metric: 'Attribution Tracking', viptant: 'Multi-touch semantic mapping', wrapper: 'Single-source static cookies' },
    { metric: 'Reporting Speed', viptant: 'Real-time pipeline sync', wrapper: '48-hour data lag times' },
    { metric: 'Forecasting Logic', viptant: 'Predictive regression algorithms', wrapper: 'Manual Excel line extrapolation' },
    { metric: 'AI Diagnostic Loop', viptant: 'Automatic root-cause detection', wrapper: 'Manual analyst lookup audits' },
    { metric: 'Integrations Scope', viptant: 'Direct REST + database bindings', wrapper: 'Brittle CSV upload procedures' },
  ];

  const faqs = [
    { q: 'How does Viptant solve attribution cookie blocks?', a: 'We use server-side tracking, native API connection points, and semantic identity resolution logs to map conversion journeys without relying entirely on browser cookies.' },
    { q: 'Can I export analytics data?', a: 'Yes. All charts and data tables can be exported as CSV, JSON, or integrated directly with BigQuery and Snowflake on Enterprise plans.' },
    { q: 'How long does data retention last?', a: 'We retain telemetry logs and conversion history for up to 3 years on Pro plans, and offer unlimited custom data residency retention on Enterprise plans.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 overflow-hidden bg-grid-dots">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 text-left">
            <FadeUp>
              <SectionLabel>Data Telemetry</SectionLabel>
              <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 leading-tight">
                Understand Every Marketing Touchpoint
              </GradientHeading>
              <p className="text-neutral-400 text-sm sm:text-base leading-relaxed max-w-xl mb-8">
                Clean telemetry, multi-channel attribution, and predictive modeling algorithms. Understand exactly what campaign copy drives your pipeline.
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
                  Request Data Audit
                </Button>
              </div>
            </FadeUp>
          </div>

          {/* Analytics Forecast Mockup */}
          <div className="lg:col-span-5">
            <FadeUp delay={0.2} className="relative rounded-2xl border border-white/10 bg-neutral-950/80 p-5 glass overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3.5 mb-5">
                <span className="text-xs font-semibold text-neutral-300 flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4 text-violet-400" /> Forecasting Engine
                </span>
                <span className="px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-[9px] text-violet-400 font-mono">ANALYTICS</span>
              </div>

              {/* KPI Metrics */}
              <div className="p-4 rounded-xl bg-neutral-900 border border-white/5 mb-5 space-y-3">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="text-neutral-400">Current Q3 Pipeline:</span>
                  <span className="text-white font-bold">$1.84M</span>
                </div>

                <div className="border-t border-white/5 pt-3 space-y-2 text-[9px] font-mono">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Q4 Projection:</span>
                    <span className={projected ? 'text-emerald-400 font-bold' : 'text-white'}>
                      {projected ? '$2.48M (+34%)' : '$1.92M (Flat)'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Attribution Model:</span>
                    <span className="text-white">Linear Multi-Touch</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Data Integrity Score:</span>
                    <span className="text-emerald-400 font-bold">99.8% (Clean)</span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <Button
                variant={projected ? "outline" : "violet"}
                onClick={simulateForecasting}
                className="w-full h-9 text-[10px] gap-2"
                isLoading={loading}
                disabled={projected}
              >
                {projected ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" /> Forecast Rendered
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-3.5 h-3.5" /> Run Q4 Pipeline Forecast
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
              <SectionLabel>Core Capabilities</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Five Engines of Unified Analytics
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
                Advanced Telemetry Infrastructure
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
                Analytics vs. Legacy Reports
              </GradientHeading>
            </FadeUp>
          </div>

          <FadeUp delay={0.1} className="rounded-xl border border-white/6 overflow-hidden bg-black shadow-xl">
            <div className="grid grid-cols-3 p-4 bg-neutral-900/50 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-neutral-400 border-b border-white/5">
              <span>Capability</span>
              <span>Viptant Analytics</span>
              <span>Legacy BI</span>
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
              <SectionLabel>Analytics FAQ</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Common Analytics Questions
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
              Get Started with Analytics
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Enable real-time tracking. Hook your pipelines and begin optimizing campaign outputs with clean telemetry.
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
                Schedule Data Review
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
