'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, Cpu, Library, Database, Bot, BarChart3, 
  ArrowRight, Shield, Zap, RefreshCw, CheckCircle2, ChevronRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function AIWorkspacePage() {
  const router = useRouter();
  
  // State for AI Gateway Routing mockup simulator
  const [selectedModel, setSelectedModel] = React.useState('gemini');
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState('Click "Route Request" to simulate AI Gateway routing...');

  const simulateRoute = (model: string) => {
    setLoading(true);
    setSelectedModel(model);
    setResult('Orchestrator evaluating request complexity...');
    
    setTimeout(() => {
      setLoading(false);
      if (model === 'gemini') {
        setResult('Routed to Gemini 1.5 Pro. Reason: Structured output schema validation & high reasoning task. [Latency: 280ms | Tokens Saved: 15%]');
      } else if (model === 'claude') {
        setResult('Routed to Claude 3.5 Sonnet. Reason: Complex system writing & creative copy matching. [Latency: 410ms | Tokens Saved: 8%]');
      } else {
        setResult('Routed to GPT-4o. Reason: High-speed analytics processing & math function checks. [Latency: 310ms | Tokens Saved: 12%]');
      }
    }, 1000);
  };

  const pillars = [
    { icon: Cpu, name: 'AI Gateway', desc: 'A unified API proxy that manages prompt routing across Gemini, Claude, and GPT models based on speed, cost, and accuracy thresholds.' },
    { icon: Library, name: 'Prompt Platform', desc: 'Collaborative, version-controlled library to test, save, inject variables into, and validate prompt templates.' },
    { icon: Database, name: 'Knowledge Platform', desc: 'Secure vector storage pipelines (RAG) that parse company documents, brand manuals, and marketing guidelines.' },
    { icon: Bot, name: 'Intelligent Agents', desc: 'Autonomous workers designed for specialized tasks (copy writing, keyword research, lead enrichment) collaborating together.' },
    { icon: BarChart3, name: 'Agent Analytics', desc: 'Track token usage, cost optimization profiles, accuracy thresholds, and business conversion value per model.' },
  ];

  const features = [
    { title: 'Semantic Caching', desc: 'Cache similar questions to reduce LLM costs by up to 35% and serve responses in <50ms.' },
    { title: 'Isolated Vector Vault', desc: 'Tenant-isolated embeddings storage ensures your enterprise documents are never shared or leaked.' },
    { title: 'Few-Shot Injection', desc: 'Incorporate historical conversion data directly into system prompts for automated improvement.' },
    { title: 'Model-Agnostic Schemas', desc: 'Define your parameters once. Our system translates structured outputs (JSON) across all models.' },
    { title: 'Real-Time Cost Caps', desc: 'Enforce budget limits per agent and category to prevent runtime token runaways.' },
    { title: 'Prompt Diagnostics', desc: 'A/B test prompt variations against live customer CTR to identify high-performing systems.' },
  ];

  const comparisons = [
    { metric: 'Model Agility', viptant: 'Dynamic multi-model routing', wrapper: 'Hardcoded single API client' },
    { metric: 'Brand Guardrails', viptant: 'Semantic constraints filter', wrapper: 'No systemic safety checks' },
    { metric: 'RAG Integration', viptant: 'Native vector memory vault', wrapper: 'Requires manual integrations' },
    { metric: 'Structured Output', viptant: 'Cross-model schema translation', wrapper: 'Breaks when model API changes' },
    { metric: 'Token Optimization', viptant: 'Up to 35% semantic cache saves', wrapper: 'Pays full token cost always' },
  ];

  const faqs = [
    { q: 'Is my vector database secure?', a: 'Yes. Viptant implements tenant-isolated namespace indexing in our vector pipeline. Your documents, corporate credentials, and prompts are never used to train global models.' },
    { q: 'What is the gateway latency overhead?', a: 'The Viptant AI Gateway adds a negligible overhead of <15ms. Most users save latency overall by leveraging model caching and fast-routing algorithms.' },
    { q: 'Can I route prompts to my fine-tuned local models?', a: 'Yes. Enterprise plans support connecting custom endpoints (such as Llama-3 running in your private VPC) to the AI Gateway.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 overflow-hidden bg-grid-dots">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 text-left">
            <FadeUp>
              <SectionLabel>Core Platform</SectionLabel>
              <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 leading-tight">
                The Central Brain for Enterprise AI
              </GradientHeading>
              <p className="text-neutral-400 text-sm sm:text-base leading-relaxed max-w-xl mb-8">
                Connect knowledge bases, manage prompt templates, route requests dynamically to top LLMs, and orchestrate network-isolated AI agents in one unified system.
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
                  Request Dedicated Demo
                </Button>
              </div>
            </FadeUp>
          </div>

          {/* AI Gateway Routing Simulator */}
          <div className="lg:col-span-5">
            <FadeUp delay={0.2} className="relative rounded-2xl border border-white/10 bg-neutral-950/80 p-5 glass overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3.5 mb-5">
                <span className="text-xs font-semibold text-neutral-300 flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-violet-400" /> AI Gateway Proxy
                </span>
                <span className="px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-[9px] text-violet-400 font-mono">SIMULATION</span>
              </div>

              {/* Selector Buttons */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                {['gemini', 'claude', 'gpt'].map((m) => (
                  <button
                    key={m}
                    onClick={() => setSelectedModel(m)}
                    className={`py-2 rounded-lg text-[10px] font-mono border transition-all cursor-pointer ${
                      selectedModel === m
                        ? 'bg-violet-600 border-violet-500 text-white font-bold'
                        : 'bg-neutral-900 border-white/5 text-neutral-500 hover:text-neutral-300'
                    }`}
                  >
                    {m.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Prompt Box */}
              <div className="p-3.5 rounded-lg bg-neutral-900 border border-white/5 text-[10px] font-mono mb-4 text-neutral-400">
                POST /api/v1/gateway/chat <br />
                <span className="text-neutral-500">{"{"} prompt: "Optimize social campaign copy" {"}"}</span>
              </div>

              {/* Trigger Button */}
              <Button
                variant="violet"
                onClick={() => simulateRoute(selectedModel)}
                className="w-full h-9 text-[10px] gap-2 mb-4"
                isLoading={loading}
              >
                <RefreshCw className="w-3 h-3" /> Route Request
              </Button>

              {/* Results Console */}
              <div className="p-3.5 rounded-lg bg-black border border-white/8 text-[9px] font-mono text-emerald-400 min-h-[64px] flex items-center">
                {result}
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
              <SectionLabel>How It Works</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Five Foundations of AI Workspace
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
                Engineered for Enterprise Operations
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
              <SectionLabel>Architecture Comparison</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Why Viptant Beats Raw APIs
              </GradientHeading>
            </FadeUp>
          </div>

          <FadeUp delay={0.1} className="rounded-xl border border-white/6 overflow-hidden bg-black shadow-xl">
            <div className="grid grid-cols-3 p-4 bg-neutral-900/50 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-neutral-400 border-b border-white/5">
              <span>Capability</span>
              <span>Viptant OS</span>
              <span>Generic Wrappers</span>
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
              <SectionLabel>Workspace FAQ</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Common Technical Questions
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
              Get Started with the AI Workspace
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Orchestrate models, clean databases, and automate your brand operations inside our compliant framework.
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
                Schedule Architecture Call
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
