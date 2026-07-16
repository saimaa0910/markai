'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, Sparkles, LayoutGrid, CheckCircle2, ChevronRight,
  ArrowRight, Search, Zap, Check, RefreshCw, PenTool 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function ContentStudioPage() {
  const router = useRouter();

  // State for interactive text generation simulator
  const [generated, setGenerated] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [typedText, setTypedText] = React.useState('');

  const sampleCopy = "Subject: Automate your brand operations with Viptant AI Agents...\n\nHi there,\n\nWe're excited to introduce the world's first AI-Native Marketing OS. Create, publish and audit campaign copies on autopilot. Your 14-day trial is ready...";

  const simulateGeneration = () => {
    setLoading(true);
    setGenerated(false);
    setTypedText('');
    
    setTimeout(() => {
      setLoading(false);
      setGenerated(true);
      
      // Simulate typing speed
      let idx = 0;
      const timer = setInterval(() => {
        if (idx < sampleCopy.length) {
          setTypedText(sampleCopy.slice(0, idx + 1));
          idx += 3; // speed up typing
        } else {
          clearInterval(timer);
        }
      }, 20);
    }, 1000);
  };

  const pillars = [
    { icon: PenTool, name: 'AI Writer', desc: 'Generate brand-aligned content in seconds. Features isolated contextual prompts to preserve voice tone.' },
    { icon: Sparkles, name: 'Prompt Gallery', desc: 'Access pre-built, conversion-optimized templates for emails, LinkedIn feeds, and Google Ads copy.' },
    { icon: FileText, name: 'Long-Form Creator', desc: 'Draft 2,000-word blog posts complete with keyword structures, meta tags, and alt text suggestions.' },
    { icon: LayoutGrid, name: 'Structured Ads', desc: 'Generate high-performance variations optimized for character limits and click triggers per platform.' },
  ];

  const features = [
    { title: 'Brand Safety Guardrails', desc: 'Verify generated outputs against strict brand guidelines, plagiarism indexes, and legal restrictions.' },
    { title: 'Semantic Keyword Sync', desc: 'Incorporate active SEO terms naturally into draft outputs to maintain high search engines ranking.' },
    { title: 'Cohort Personalization', desc: 'Draft custom copy variations tailored to specific buyer persona tags automatically.' },
    { title: 'Dynamic Variables', desc: 'Inject customer metadata (e.g. Company, ARR, Role) seamlessly into generated text files.' },
    { title: 'Multi-Language Outputs', desc: 'Generate localized brand content in 24 languages with native translation safety checking.' },
    { title: 'Interactive Previews', desc: 'Review how copy renders in Gmail feeds, search results, or social timelines instantly.' },
  ];

  const comparisons = [
    { metric: 'Brand Voice Sync', viptant: 'Guaranteed via vector profiles', wrapper: 'Unpredictable generic outputs' },
    { metric: 'Compliance Validation', viptant: 'Automatic built-in schema checks', wrapper: 'Manual verification needed' },
    { metric: 'Multi-Channel Adapts', viptant: 'Creates matching sets in one click', wrapper: 'Requires separate inputs per post' },
    { metric: 'Keyword Injection', viptant: 'Optimizes content for active SEO', wrapper: 'Basic keyword stuffing lists' },
    { metric: 'Attribution Loops', viptant: 'Learns from historical CTR logs', wrapper: 'Static model responses always' },
  ];

  const faqs = [
    { q: 'How does Viptant learn our brand voice?', a: 'You upload brand manuals, historical copy, style guidelines, and product specs to the Knowledge Platform. Our agents reference these documents as vector contexts for all tasks.' },
    { q: 'Is the generated content unique?', a: 'Yes. Every generated draft is built on-the-fly and checked against standard plagiarism filters to guarantee originality.' },
    { q: 'Can we edit the outputs directly?', a: 'Yes. The Content Studio includes an interactive editor so your writing team can modify, approve, or regenerate any sentence.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 overflow-hidden bg-grid-dots">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 text-left">
            <FadeUp>
              <SectionLabel>Content Engine</SectionLabel>
              <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 leading-tight">
                Scale Brand Content with AI Accuracy
              </GradientHeading>
              <p className="text-neutral-400 text-sm sm:text-base leading-relaxed max-w-xl mb-8">
                Generate emails, blogs, ads, and social media copy that sounds exactly like your writing team. Guided by brand vectors, safety rules, and SEO metrics.
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
                  Book Demo
                </Button>
              </div>
            </FadeUp>
          </div>

          {/* Copy Writer Mockup */}
          <div className="lg:col-span-5">
            <FadeUp delay={0.2} className="relative rounded-2xl border border-white/10 bg-neutral-950/80 p-5 glass overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3.5 mb-5">
                <span className="text-xs font-semibold text-neutral-300 flex items-center gap-1.5">
                  <PenTool className="w-4 h-4 text-violet-400" /> AI Document Studio
                </span>
                <span className="px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-[9px] text-violet-400 font-mono">EDITOR</span>
              </div>

              {/* Input Prompt */}
              <div className="p-3.5 rounded-lg bg-neutral-900 border border-white/5 text-[9px] font-mono mb-4 text-neutral-400">
                Template: Outbound Announcement Email <br />
                Goal: Introduce Viptant to tech cohort <br />
                Tone: Professional, Innovative
              </div>

              {/* Editor Console */}
              <div className="p-3.5 rounded-lg bg-black border border-white/8 text-[9px] font-mono text-neutral-300 min-h-[120px] mb-4 whitespace-pre-line leading-relaxed select-none">
                {loading ? 'Analyzing brand guidelines and generating copy...' : typedText || 'Click Generate to compose document...'}
                {!loading && generated && typedText.length < sampleCopy.length && (
                  <span className="w-1 h-3 bg-violet-500 ml-0.5 animate-pulse inline-block" />
                )}
              </div>

              {/* Action Trigger */}
              <Button
                variant={generated && typedText.length === sampleCopy.length ? "outline" : "violet"}
                onClick={simulateGeneration}
                className="w-full h-9 text-[10px] gap-2"
                isLoading={loading}
                disabled={loading || (generated && typedText.length < sampleCopy.length)}
              >
                <Sparkles className="w-3.5 h-3.5" /> Generate Copy
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
              <SectionLabel>Capabilities</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Four Pillars of Content Studio
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
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
                Brand-First Copywriting Systems
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
              <SectionLabel>Capabilities Comparison</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Content Studio vs. Generic AI Writers
              </GradientHeading>
            </FadeUp>
          </div>

          <FadeUp delay={0.1} className="rounded-xl border border-white/6 overflow-hidden bg-black shadow-xl">
            <div className="grid grid-cols-3 p-4 bg-neutral-900/50 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-neutral-400 border-b border-white/5">
              <span>Capability</span>
              <span>Viptant Content Studio</span>
              <span>ChatGPT / Writing Wrappers</span>
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
              <SectionLabel>Content FAQ</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Common Writing Questions
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
              Get Started with Content Studio
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Enable your copywriters. Scale on-brand templates and personalizes campaign outlines with strict security parameters.
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
                Connect Writers Team
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
