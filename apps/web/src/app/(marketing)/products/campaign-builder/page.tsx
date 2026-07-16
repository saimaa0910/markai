'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Megaphone, Calendar, BarChart2, LayoutTemplate, Share2, 
  ArrowRight, Sparkles, Check, CheckCircle2, ChevronRight, Play 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function CampaignBuilderPage() {
  const router = useRouter();

  // State for interactive schedule simulator
  const [optimized, setOptimized] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const simulateOptimization = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setOptimized(true);
    }, 1200);
  };

  const pillars = [
    { icon: Megaphone, name: 'Goal Campaigns', desc: 'Define high-level objectives (e.g. "Drive SaaS signups") and let agents generate all relevant assets.' },
    { icon: Calendar, name: 'Smart Scheduling', desc: 'Predictive timing models release posts when your audience is most active based on conversion history.' },
    { icon: BarChart2, name: 'Performance Loop', desc: 'Agents monitor click rates in real time and edit downstream copy to optimize performance on the fly.' },
    { icon: LayoutTemplate, name: 'Asset Templates', desc: 'Create reusable layout parameters that ensure every agent-created asset remains on-brand.' },
    { icon: Share2, name: 'Multi-Channel Publishing', desc: 'Deploy assets seamlessly across Google Ads, Meta Business Suite, LinkedIn, X, and email servers.' },
  ];

  const features = [
    { title: 'A/B Variant Generation', desc: 'Create up to 10 copy variants per channel, structured automatically for rapid cohort testing.' },
    { title: 'Semantic Drift Filters', desc: 'Monitor scheduled posts to ensure they align with brand voice guidelines over time.' },
    { title: 'Direct Publisher Mappings', desc: 'Authorize accounts once. Viptant publishes drafts or schedules releases natively via API.' },
    { title: 'Conversion Attribution', desc: 'Evaluate which specific copy variation or channel triggered conversions.' },
    { title: 'Auto-Budget Throttling', desc: 'Throttles ad budgets automatically if click costs surpass target CPA thresholds.' },
    { title: 'Interactive Previews', desc: 'Review scheduled drafts on desktop, mobile, and feed mockups before they launch.' },
  ];

  const comparisons = [
    { metric: 'Workflow Orchestration', viptant: 'Goal-driven self-scheduling', wrapper: 'Manual drag-and-drop calendars' },
    { metric: 'Copy Adaptation', viptant: 'Autonomously edits underperforming ads', wrapper: 'Requires manual marketer rewrites' },
    { metric: 'Attribution Tracking', viptant: 'Dynamic semantic tagging per lead', wrapper: 'Basic static UTM parameter tags' },
    { metric: 'Publishing Method', viptant: 'Native automated API triggers', wrapper: 'Logged in copy-paste manual release' },
    { metric: 'Safety Checks', viptant: 'Continuous brand alignment validation', wrapper: 'Rely on manual human verification' },
  ];

  const faqs = [
    { q: 'How do agents know when to post?', a: 'Viptant evaluates historical engagement logs from your connected channels and uses predictive regression to schedule releases at peak conversion hours.' },
    { q: 'Can I review posts before they are published?', a: 'Yes. By default, Viptant puts all AI-generated campaigns into "Draft Review" state. You can toggle "Autopilot" when you are confident in an agent\'s performance.' },
    { q: 'What channels are supported?', a: 'We support LinkedIn Pages, Meta Ads (Facebook & Instagram), Google Ads, YouTube Shorts, X (formerly Twitter), HubSpot Email, and Mailchimp.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 overflow-hidden bg-grid-dots">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 text-left">
            <FadeUp>
              <SectionLabel>Channel Distribution</SectionLabel>
              <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 leading-tight">
                Orchestrate Campaigns on Autopilot
              </GradientHeading>
              <p className="text-neutral-400 text-sm sm:text-base leading-relaxed max-w-xl mb-8">
                Connect your brand channels and let Viptant agents compose, schedule, and optimize multi-channel copy to reach target conversion goals.
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
                  Schedule Demo
                </Button>
              </div>
            </FadeUp>
          </div>

          {/* Schedule Optimization Mockup */}
          <div className="lg:col-span-5">
            <FadeUp delay={0.2} className="relative rounded-2xl border border-white/10 bg-neutral-950/80 p-5 glass overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3.5 mb-5">
                <span className="text-xs font-semibold text-neutral-300 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-violet-400" /> Campaign Schedule
                </span>
                <span className="px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-[9px] text-violet-400 font-mono">CALENDAR</span>
              </div>

              {/* Scheduled Item Card */}
              <div className="p-4 rounded-xl bg-neutral-900 border border-white/5 mb-5 space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-xs font-bold text-white">LinkedIn: "Q4 Launch Ad"</h4>
                    <p className="text-[9px] text-neutral-500">Copy variant v2-AB</p>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-violet-500/15 border border-violet-500/20 text-[8px] font-bold text-violet-400">READY</span>
                </div>

                <div className="border-t border-white/5 pt-3 space-y-2 text-[9px] font-mono">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Suggested Time:</span>
                    <span className={optimized ? 'text-emerald-400 font-bold' : 'text-white'}>
                      {optimized ? '2:15 PM EST (Optimal)' : '8:00 AM EST (Standard)'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Predicted CTR:</span>
                    <span className={optimized ? 'text-emerald-400 font-bold' : 'text-white'}>
                      {optimized ? '4.82% (+40%)' : '3.41%'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Optimization basis:</span>
                    <span className="text-neutral-300 truncate max-w-[150px]">
                      {optimized ? 'Model detects high activity cohort' : 'Standard scheduler template'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <Button
                variant={optimized ? "outline" : "violet"}
                onClick={simulateOptimization}
                className="w-full h-9 text-[10px] gap-2"
                isLoading={loading}
                disabled={optimized}
              >
                {optimized ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" /> Schedule Optimized
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" /> Optimize Schedule with AI
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
              <SectionLabel>Key Pillars</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Five Engines of Campaign builder
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
                End-to-End Asset Orchestration
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
                Campaign builder vs. Traditional Schedulers
              </GradientHeading>
            </FadeUp>
          </div>

          <FadeUp delay={0.1} className="rounded-xl border border-white/6 overflow-hidden bg-black shadow-xl">
            <div className="grid grid-cols-3 p-4 bg-neutral-900/50 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-neutral-400 border-b border-white/5">
              <span>Capability</span>
              <span>Viptant Builder</span>
              <span>Traditional Tools</span>
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
              <SectionLabel>Builder FAQ</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Common Campaign Questions
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
              Get Started with Campaign Builder
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Enable your agents. Build optimized delivery slots and launch conversion campaigns across channels instantly.
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
                Connect Channels Talk
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
