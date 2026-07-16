'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GitBranch, Play, AlertCircle, ArrowRight, Sparkles, 
  Check, CheckCircle2, ChevronRight, Bell, Calendar, Cpu 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function AutomationPage() {
  const router = useRouter();

  // State for interactive workflow simulation
  const [step, setStep] = React.useState(0);
  const [loading, setLoading] = React.useState(false);

  const simulateWorkflow = () => {
    setLoading(true);
    setStep(1);
    
    // Animate flow steps
    setTimeout(() => {
      setStep(2);
      setTimeout(() => {
        setStep(3);
        setLoading(false);
      }, 1000);
    }, 1000);
  };

  const resetWorkflow = () => {
    setStep(0);
  };

  const pillars = [
    { icon: GitBranch, name: 'AI Workflows', desc: 'Build complex, multi-agent loops that run autonomously until they reach specified conversion success parameters.' },
    { icon: Play, name: 'Smart Triggers', desc: 'Trigger workflows instantly via webhook alerts, Stripe payments, new CRM records, or calendar slots booking.' },
    { icon: Cpu, name: 'Agent Actions', desc: 'Instruct specialized agents to scrape sites, clean copy, generate visual layouts, or post to channels.' },
    { icon: Calendar, name: 'Queue Scheduling', desc: 'Run jobs on cron timers, delay actions until conversion peaks, or throttle speeds based on API rate limits.' },
    { icon: Bell, name: 'Alerts & Webhooks', desc: 'Notify your marketing team immediately via Slack, Microsoft Teams, or email when campaigns complete.' },
  ];

  const features = [
    { title: 'Self-Correcting Retries', desc: 'If an ad channel API fails, our queue manager schedules retries automatically with exponential backoffs.' },
    { title: 'Semantic Branching', desc: 'Branch workflows based on copy intent or lead size (e.g. "If lead is enterprise, route to Slack, else send nurture email").' },
    { title: 'Isolated Workspace Runs', desc: 'Each trigger execution runs inside an isolated sandbox memory container to ensure data privacy.' },
    { title: 'Visual Flow Canvas', desc: 'Understand your marketing architecture visually. Monitor paths, latency, and success rates at a glance.' },
    { title: 'API Rate-Limit Protection', desc: 'Queue triggers automatically to prevent exceeding Salesforce, Google, or OpenAI daily limits.' },
    { title: 'Event Auditing', desc: 'Review comprehensive logs of every model call, prompt variable injection, and channel post made.' },
  ];

  const comparisons = [
    { metric: 'Logic Handling', viptant: 'Semantic decisions by AI agents', wrapper: 'Rigid linear IF/THEN coding' },
    { metric: 'Error Resilience', viptant: 'Autonomously adapts and retries', wrapper: 'Fails immediately and breaks' },
    { metric: 'Data Context', viptant: 'Shares shared vector memory vault', wrapper: 'No persistent context history' },
    { metric: 'Setup Friction', viptant: 'Describe workflow in text prompts', wrapper: 'Manual API webhook mapping' },
    { metric: 'Latency Management', viptant: 'Dynamic queue throttling', wrapper: 'Static timed delayed buffers' },
  ];

  const faqs = [
    { q: 'How does semantic branching work?', a: 'Instead of strict logic (like "if email contains acme"), Viptant uses a small reasoning model to evaluate the lead company profile. For example, it evaluates if "Acme Corp is a prospective B2B buyer," then routes accordingly.' },
    { q: 'Can we build custom webhooks?', a: 'Yes. Viptant offers custom inbound webhooks so you can trigger campaigns from any external application, app, or database.' },
    { q: 'Is there an execution retry limit?', a: 'By default, the system retries failed API calls up to 5 times over a 2-hour window. You can adjust limits per workflow.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 overflow-hidden bg-grid-dots">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 text-left">
            <FadeUp>
              <SectionLabel>Process Automation</SectionLabel>
              <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 leading-tight">
                Self-Correcting Marketing Workflows
              </GradientHeading>
              <p className="text-neutral-400 text-sm sm:text-base leading-relaxed max-w-xl mb-8">
                Connect your business triggers to intelligent agent networks. Build self-optimizing loops that generate copy, verify branding, and post autonomously.
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
                  Request Architecture Call
                </Button>
              </div>
            </FadeUp>
          </div>

          {/* Workflow Simulator Mockup */}
          <div className="lg:col-span-5">
            <FadeUp delay={0.2} className="relative rounded-2xl border border-white/10 bg-neutral-950/80 p-5 glass overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3.5 mb-5">
                <span className="text-xs font-semibold text-neutral-300 flex items-center gap-1.5">
                  <GitBranch className="w-4 h-4 text-violet-400" /> Automation Flow
                </span>
                <span className="px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-[9px] text-violet-400 font-mono">FLOWCHART</span>
              </div>

              {/* Node-Based Layout visualization */}
              <div className="space-y-3.5 mb-5">
                {/* Node 1 */}
                <div className={`p-2.5 rounded-lg border text-[9px] font-mono flex items-center justify-between transition-colors ${
                  step >= 1 ? 'border-violet-500 bg-violet-600/5 text-white' : 'border-white/5 bg-neutral-900 text-neutral-500'
                }`}>
                  <span>[Trigger] Inbound Lead Logged</span>
                  {step >= 1 && <span className="text-violet-400 font-bold">✓ RUNNING</span>}
                </div>

                {/* Arrow */}
                <div className="h-4 flex justify-center"><div className="w-px h-full bg-white/10" /></div>

                {/* Node 2 */}
                <div className={`p-2.5 rounded-lg border text-[9px] font-mono flex items-center justify-between transition-colors ${
                  step >= 2 ? 'border-violet-500 bg-violet-600/5 text-white' : 'border-white/5 bg-neutral-900 text-neutral-500'
                }`}>
                  <span>[Agent] Analyze Company Size & Score</span>
                  {step >= 2 && <span className="text-violet-400 font-bold">✓ COMPLETED</span>}
                </div>

                {/* Arrow */}
                <div className="h-4 flex justify-center"><div className="w-px h-full bg-white/10" /></div>

                {/* Node 3 */}
                <div className={`p-2.5 rounded-lg border text-[9px] font-mono flex items-center justify-between transition-colors ${
                  step >= 3 ? 'border-emerald-500 bg-emerald-600/5 text-white' : 'border-white/5 bg-neutral-900 text-neutral-500'
                }`}>
                  <span>[Branch] If Score &gt; 80: Slack Alert + Demo invite</span>
                  {step >= 3 && <span className="text-emerald-400 font-bold">✓ DISPATCHED</span>}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  variant="violet"
                  onClick={simulateWorkflow}
                  className="flex-1 h-9 text-[10px] gap-2"
                  isLoading={loading}
                  disabled={step > 0}
                >
                  <Play className="w-3 h-3 animate-pulse" /> Run Test Flow
                </Button>
                {step > 0 && (
                  <Button variant="outline" onClick={resetWorkflow} className="h-9 px-3 text-[10px] text-neutral-400 border-white/5">
                    Reset
                  </Button>
                )}
              </div>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* ─── Platform Pillars Section ───────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <FadeUp>
              <SectionLabel>Core Pillars</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Five Engines of Agentic Automation
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
                Intelligent Action Pipelines
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
                Viptant Workflows vs. Legacy Triggers
              </GradientHeading>
            </FadeUp>
          </div>

          <FadeUp delay={0.1} className="rounded-xl border border-white/6 overflow-hidden bg-black shadow-xl">
            <div className="grid grid-cols-3 p-4 bg-neutral-900/50 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-neutral-400 border-b border-white/5">
              <span>Capability</span>
              <span>Viptant Workflows</span>
              <span>Traditional Tools (Zapier)</span>
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
              <SectionLabel>Automation FAQ</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Common Automation Questions
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
              Get Started with Automation
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Enable your agents. Schedule task chains, handle API queues, and scale automated campaigns securely.
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
                Build Custom Workflow
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
