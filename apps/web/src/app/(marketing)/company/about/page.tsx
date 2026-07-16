'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, Target, Eye, Shield, Users, Rocket, Brain, 
  Cpu, Zap, ArrowRight, CheckCircle2, ChevronRight, Award
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  FadeUp, GradientHeading, SectionLabel, StatCard 
} from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function AboutPage() {
  const router = useRouter();

  const values = [
    {
      icon: Brain,
      title: 'AI-First Paradigm',
      desc: 'We do not just add AI features. We build autonomous agent-first systems that redefine how work gets done.',
    },
    {
      icon: Target,
      title: 'Extreme Precision',
      desc: 'Marketing is a science. We design our algorithms and pipelines for maximum ROI, deterministic accuracy, and clean data.',
    },
    {
      icon: Shield,
      title: 'Enterprise-Grade Trust',
      desc: 'Security, privacy, and compliance are non-negotiable. Your data is protected by industry-leading isolation and safety standards.',
    },
    {
      icon: Users,
      title: 'Human-Agent Synergy',
      desc: 'Our platform is designed to multiply human creativity, not replace it, creating a seamless workflow between marketers and AI.',
    },
    {
      icon: Rocket,
      title: 'Continuous Velocity',
      desc: 'We iterate relentlessly. Our platform adapts to new models, trends, and technologies overnight so you are never left behind.',
    },
    {
      icon: Award,
      title: 'Design Excellence',
      desc: 'We believe enterprise tools should be as intuitive and delightful to use as the best consumer products.',
    },
  ];

  const leadership = [
    {
      name: 'Alex Rivera',
      role: 'Co-Founder & CEO',
      bio: 'Former Head of AI Product at Vercel. Led teams building state-of-the-art developer tooling.',
      initials: 'AR',
      bg: 'from-violet-600/30 to-indigo-600/30',
    },
    {
      name: 'Dr. Sarah Chen',
      role: 'Co-Founder & Chief Scientist',
      bio: 'PhD in NLP from Stanford. Previously Lead Research Scientist at Google DeepMind working on LLM reasoning.',
      initials: 'SC',
      bg: 'from-fuchsia-600/30 to-pink-600/30',
    },
    {
      name: 'Marcus Vance',
      role: 'VP of Engineering',
      bio: 'Former Principal Architect at Databricks. Expert in distributed systems and high-throughput databases.',
      initials: 'MV',
      bg: 'from-blue-600/30 to-cyan-600/30',
    },
    {
      name: 'Elena Rostova',
      role: 'Head of Design',
      bio: 'Former Lead UI/UX Designer at Stripe. Passionate about crafting premium, high-fidelity user experiences.',
      initials: 'ER',
      bg: 'from-amber-600/30 to-rose-600/30',
    },
  ];

  const milestones = [
    {
      year: '2024',
      title: 'Company Inception',
      desc: 'Viptant was founded with a vision to build a centralized operating system for agentic marketing, raising $6M in Seed funding.',
    },
    {
      year: '2025',
      title: 'V1 Launch & Series A',
      desc: 'Released the Core Prompt & Knowledge Platforms. Secured $24M in Series A funding led by top-tier enterprise software investors.',
    },
    {
      year: '2026',
      title: 'Enterprise AI Workspace',
      desc: 'Launched autonomous multi-agent workspaces, reaching over 2,000+ marketing teams globally with SOC 2 compliance.',
    },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 md:pt-32 md:pb-28 overflow-hidden bg-grid-dots">
        {/* Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] rounded-full bg-violet-600/10 blur-[140px] pointer-events-none" />
        <div className="absolute top-1/3 left-1/3 w-[300px] h-[300px] rounded-full bg-indigo-500/5 blur-[100px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>About Viptant</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 max-w-4xl mx-auto leading-tight">
              Rewriting the Rules of Marketing with AI Agents
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-base sm:text-xl text-neutral-400 max-w-2xl mx-auto leading-relaxed mb-10">
              We are building the Enterprise AI Marketing Operating System. Empowering teams to orchestrate autonomous workflows, scale brand operations, and optimize performance in real time.
            </p>
          </FadeUp>
          <FadeUp delay={0.3}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button 
                variant="violet" 
                size="lg"
                onClick={() => router.push('/auth/register')}
                className="w-full sm:w-auto h-12 font-semibold"
              >
                Start Free Trial <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
              <Button 
                variant="outline" 
                size="lg"
                onClick={() => router.push('/company/contact')}
                className="w-full sm:w-auto h-12 text-neutral-300 hover:text-white"
              >
                Contact Sales
              </Button>
            </div>
          </FadeUp>

          {/* Quick Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto mt-20 pt-10 border-t border-white/5">
            <FadeUp delay={0.4}>
              <StatCard value="2,000" label="Active Teams" suffix="+" />
            </FadeUp>
            <FadeUp delay={0.5}>
              <StatCard value="12M" label="Generated Creatives" suffix="+" />
            </FadeUp>
            <FadeUp delay={0.6}>
              <StatCard value="99.99" label="Uptime SLA" suffix="%" />
            </FadeUp>
            <FadeUp delay={0.7}>
              <StatCard value="$30M" label="Funding Raised" />
            </FadeUp>
          </div>
        </div>
      </section>

      {/* ─── Mission & Vision Section ───────────────────────────────────── */}
      <section className="py-20 border-t border-white/5 relative">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Mission */}
          <FadeUp className="relative overflow-hidden rounded-2xl border border-white/8 bg-neutral-950/40 p-8 md:p-12 glass">
            <div className="absolute top-0 right-0 w-[200px] h-[200px] rounded-full bg-violet-600/5 blur-[80px]" />
            <div className="w-12 h-12 rounded-xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400 mb-6">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-bold mb-4 text-white">Our Mission</h3>
            <p className="text-neutral-400 leading-relaxed text-sm md:text-base">
              To eliminate the operational overhead of marketing campaigns, permitting teams to transition from manual execution to strategic oversight. We enable companies to scale their voice without expanding complexity.
            </p>
          </FadeUp>

          {/* Vision */}
          <FadeUp delay={0.1} className="relative overflow-hidden rounded-2xl border border-white/8 bg-neutral-950/40 p-8 md:p-12 glass">
            <div className="absolute top-0 right-0 w-[200px] h-[200px] rounded-full bg-indigo-600/5 blur-[80px]" />
            <div className="w-12 h-12 rounded-xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-6">
              <Eye className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-bold mb-4 text-white">Our Vision</h3>
            <p className="text-neutral-400 leading-relaxed text-sm md:text-base">
              A future where brand engines run on a unified, self-optimizing network of specialized AI agents. Marketing adapts in real-time, executing tasks autonomously while remaining perfectly aligned with human values and guidelines.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Story Section ────────────────────────────────────────────────── */}
      <section className="py-20 bg-neutral-950/40 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            <div className="lg:col-span-5">
              <FadeUp>
                <SectionLabel>Our Story</SectionLabel>
                <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2 mb-6">
                  Born Out of Operational Frustration
                </GradientHeading>
                <p className="text-neutral-400 leading-relaxed mb-6">
                  Marketing operations are broken. Teams spend 80% of their time copying data across platforms, formatting prompt chains, uploading creative variations, and managing scheduling boards—leaving only 20% for creative strategy.
                </p>
                <p className="text-neutral-400 leading-relaxed">
                  We started Viptant to build a unified system where developers, marketers, and AI agents collaborate seamlessly. An operating system that connects knowledge bases, LLMs, and channel triggers into one single source of truth.
                </p>
              </FadeUp>
            </div>
            <div className="lg:col-span-7 lg:pl-10">
              <FadeUp delay={0.2} className="relative border-l border-white/10 pl-6 space-y-12">
                {milestones.map((m, i) => (
                  <div key={m.year} className="relative">
                    {/* Circle timeline indicator */}
                    <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-violet-600 border-4 border-black" />
                    <span className="text-violet-400 font-mono text-sm font-semibold">{m.year}</span>
                    <h4 className="text-lg font-bold text-white mt-1 mb-2">{m.title}</h4>
                    <p className="text-neutral-500 text-sm leading-relaxed">{m.desc}</p>
                  </div>
                ))}
              </FadeUp>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Core Values Section ────────────────────────────────────────── */}
      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <FadeUp>
              <SectionLabel>Core Values</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Principles That Guide Us
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {values.map((v, i) => {
              const Icon = v.icon;
              return (
                <FadeUp 
                  key={v.title} 
                  delay={i * 0.05} 
                  className="p-8 rounded-xl border border-white/6 bg-neutral-950/20 hover:border-violet-500/20 hover:bg-neutral-900/10 transition-all group duration-300"
                >
                  <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-neutral-400 group-hover:text-violet-400 group-hover:border-violet-500/20 transition-all mb-5">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h4 className="text-lg font-bold text-white mb-2.5">{v.title}</h4>
                  <p className="text-neutral-400 text-xs md:text-sm leading-relaxed">{v.desc}</p>
                </FadeUp>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── Technology & Why Viptant Section ─────────────────────────────── */}
      <section className="py-24 bg-neutral-950/40 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <FadeUp>
              <SectionLabel>Architectural Advantage</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2 mb-6">
                Next-Gen Agent Orchestration
              </GradientHeading>
              <p className="text-neutral-400 leading-relaxed mb-6">
                Unlike simple generative wrappers, Viptant implements an advanced **Multi-Agent Orchestration Layer**. It coordinates specialized marketing agents (Content, CRM, Search, Campaigns) using shared vector knowledge contexts.
              </p>
              
              <ul className="space-y-4">
                {[
                  'Intelligent routing across Gemini, Claude & GPT systems',
                  'Isolated vector database per tenant for security',
                  'Dynamic semantic prompts optimized on conversion history',
                  'Native channel connection APIs (Google, Salesforce, HubSpot)',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-neutral-300">
                    <CheckCircle2 className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </FadeUp>

            <FadeUp delay={0.2} className="relative aspect-video rounded-2xl border border-white/10 overflow-hidden bg-neutral-950 p-6 flex flex-col justify-between">
              <div className="absolute inset-0 bg-gradient-to-tr from-violet-600/10 via-indigo-600/5 to-transparent pointer-events-none" />
              <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-violet-400" />
                  <span className="text-xs font-semibold text-neutral-300">Agentic Orchestrator v2.4</span>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[9px] text-emerald-400 font-mono">ACTIVE</span>
              </div>

              {/* Mockup Flow Visualization */}
              <div className="my-6 space-y-3.5 relative z-10">
                {[
                  { agent: 'Knowledge Base', state: 'Loaded context (14 documents)', percent: 100, color: 'bg-blue-500' },
                  { agent: 'Content Studio', state: 'Generated blog outline & copy', percent: 92, color: 'bg-violet-500' },
                  { agent: 'SEO Optimizer', state: 'Analyzing keyword densities', percent: 65, color: 'bg-amber-500' },
                ].map((m) => (
                  <div key={m.agent} className="space-y-1">
                    <div className="flex justify-between text-[10px]">
                      <span className="font-semibold text-white">{m.agent}</span>
                      <span className="text-neutral-500">{m.state}</span>
                    </div>
                    <div className="w-full h-1 bg-neutral-900 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        whileInView={{ width: `${m.percent}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 1, delay: 0.3 }}
                        className={`h-full ${m.color}`} 
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-white/5 text-[10px] text-neutral-500">
                <span>Latency: 412ms</span>
                <span>Accuracy Threshold: &gt;98.5%</span>
              </div>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* ─── Leadership Section ─────────────────────────────────────────── */}
      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <FadeUp>
              <SectionLabel>Leadership Team</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Led by Builders and Researchers
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {leadership.map((l, i) => (
              <FadeUp 
                key={l.name} 
                delay={i * 0.05} 
                className="group relative rounded-xl border border-white/6 bg-neutral-950/40 overflow-hidden flex flex-col"
              >
                {/* Visual Avatar Gradient Box */}
                <div className={`aspect-square w-full bg-gradient-to-tr ${l.bg} flex items-center justify-center relative transition-transform duration-300 group-hover:scale-105`}>
                  <span className="text-4xl font-extrabold text-white tracking-wider select-none opacity-40">{l.initials}</span>
                  <div className="absolute inset-0 bg-neutral-950/10 group-hover:bg-transparent transition-colors" />
                </div>
                
                <div className="p-6 flex-1 flex flex-col justify-between">
                  <div>
                    <h4 className="text-base font-bold text-white mb-0.5">{l.name}</h4>
                    <p className="text-xs font-semibold text-violet-400 mb-3">{l.role}</p>
                    <p className="text-xs text-neutral-400 leading-relaxed">{l.bio}</p>
                  </div>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA Banner Section ────────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50 relative overflow-hidden">
        {/* Glow */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full bg-violet-600/5 blur-[120px] pointer-events-none" />

        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <FadeUp>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-4 leading-tight">
              Ready to Upgrade to Agentic Marketing?
            </h2>
            <p className="text-neutral-400 text-sm sm:text-base max-w-lg mx-auto leading-relaxed mb-8">
              Join over 2,000+ high-performing teams automating campaigns, CRM data pipelines, and creative copy.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Button 
                variant="violet" 
                size="lg"
                onClick={() => router.push('/auth/register')}
                className="w-full sm:w-auto h-11 px-6 text-xs font-semibold"
              >
                Get Started Free <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
              <Button 
                variant="outline" 
                size="lg"
                onClick={() => router.push('/auth/login')}
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
