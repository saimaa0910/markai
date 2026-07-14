'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

// Mini mock panels rendered inline (no screenshots)
function AiWorkspaceMock() {
  return (
    <div className="rounded-xl border border-white/8 bg-neutral-950/90 overflow-hidden shadow-2xl">
      <div className="px-4 py-3 border-b border-white/5 bg-neutral-900/60 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-violet-500" />
        <span className="text-xs text-neutral-500 font-mono">AI Workspace</span>
      </div>
      <div className="p-4 space-y-3">
        <div className="flex gap-3">
          <div className="w-6 h-6 rounded-full bg-neutral-700 flex items-center justify-center text-[9px] font-bold text-neutral-300 shrink-0">AI</div>
          <div className="flex-1 px-3 py-2 rounded-lg bg-neutral-800 text-[11px] text-neutral-300 leading-relaxed">
            I've drafted your Q4 LinkedIn campaign. Based on your ICP data, I'm targeting SaaS Decision-Makers 35–50 with a thought leadership approach...
          </div>
        </div>
        <div className="flex gap-3 flex-row-reverse">
          <div className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-[9px] font-bold text-white shrink-0">U</div>
          <div className="px-3 py-2 rounded-lg bg-violet-600/20 border border-violet-500/20 text-[11px] text-violet-200">
            Make it more concise, 3 variants
          </div>
        </div>
        <div className="flex gap-3">
          <div className="w-6 h-6 rounded-full bg-neutral-700 flex items-center justify-center text-[9px] font-bold text-neutral-300 shrink-0">AI</div>
          <div className="flex-1 px-3 py-2 rounded-lg bg-neutral-800 text-[11px] text-neutral-300">
            Generated <span className="text-violet-400 font-semibold">3 variants</span> — A (Bold CTA), B (Story), C (Data-led). A has 34% higher projected CTR...
          </div>
        </div>
      </div>
    </div>
  );
}

function CrmMock() {
  const leads = [
    { name: 'Priya Sharma', title: 'VP Marketing · Acme Corp', stage: 'Proposal', value: '$45K', hot: true },
    { name: 'James Wu', title: 'CMO · TechFlow Inc', stage: 'Discovery', value: '$28K', hot: false },
    { name: 'Sofia Morales', title: 'Head of Growth · SeedBase', stage: 'Qualified', value: '$12K', hot: false },
  ];
  return (
    <div className="rounded-xl border border-white/8 bg-neutral-950/90 overflow-hidden shadow-2xl">
      <div className="px-4 py-3 border-b border-white/5 bg-neutral-900/60 flex items-center justify-between">
        <span className="text-xs text-neutral-500 font-mono">CRM Pipeline</span>
        <span className="text-[10px] text-violet-400 font-semibold bg-violet-500/10 px-2 py-0.5 rounded-full">AI Scored</span>
      </div>
      <div className="divide-y divide-white/5">
        {leads.map((l) => (
          <div key={l.name} className="px-4 py-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-neutral-800 flex items-center justify-center text-xs font-bold text-neutral-300">
                {l.name[0]}
              </div>
              <div>
                <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                  {l.name}
                  {l.hot && <span className="text-[8px] font-bold text-rose-400 bg-rose-400/10 px-1.5 rounded-full">HOT</span>}
                </div>
                <div className="text-[10px] text-neutral-500">{l.title}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <span className="text-[10px] text-neutral-400 bg-neutral-800 px-2 py-0.5 rounded-full">{l.stage}</span>
              <span className="text-xs font-bold text-emerald-400">{l.value}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalyticsMock() {
  const bars = [40, 55, 48, 70, 62, 85, 78, 92];
  return (
    <div className="rounded-xl border border-white/8 bg-neutral-950/90 overflow-hidden shadow-2xl">
      <div className="px-4 py-3 border-b border-white/5 bg-neutral-900/60 flex items-center justify-between">
        <span className="text-xs text-neutral-500 font-mono">Analytics Dashboard</span>
        <span className="text-[10px] text-emerald-400">↑ 34% vs last period</span>
      </div>
      <div className="p-4 grid grid-cols-3 gap-3 mb-4">
        {[['14.2K', 'Unique Visitors'], ['3.8%', 'Conv. Rate'], ['$4.20', 'ROAS']].map(([v, l]) => (
          <div key={l} className="flex flex-col gap-0.5">
            <span className="text-base font-extrabold text-white">{v}</span>
            <span className="text-[9px] text-neutral-500">{l}</span>
          </div>
        ))}
      </div>
      <div className="px-4 pb-4 flex items-end gap-1.5 h-20">
        {bars.map((h, i) => (
          <div
            key={i}
            className={`flex-1 rounded-sm transition-all ${i >= 5 ? 'bg-violet-500' : 'bg-neutral-700/60'}`}
            style={{ height: `${h * 0.8}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function ContentMock() {
  const items = [
    { type: 'Blog Post', title: 'How AI is Transforming B2B Marketing in 2025', status: 'Published', score: '92' },
    { type: 'Email', title: 'Q4 Customer Success Newsletter', status: 'Scheduled', score: '88' },
    { type: 'Ad Copy', title: 'LinkedIn Awareness Campaign — Variant A', status: 'Draft', score: '95' },
  ];
  return (
    <div className="rounded-xl border border-white/8 bg-neutral-950/90 overflow-hidden shadow-2xl">
      <div className="px-4 py-3 border-b border-white/5 bg-neutral-900/60 flex items-center justify-between">
        <span className="text-xs text-neutral-500 font-mono">Content Studio</span>
        <span className="text-[10px] text-violet-400 font-semibold">AI-Powered</span>
      </div>
      <div className="divide-y divide-white/5">
        {items.map((item) => (
          <div key={item.title} className="px-4 py-3 flex items-start justify-between gap-3">
            <div>
              <span className="text-[9px] font-bold uppercase tracking-wider text-violet-400">{item.type}</span>
              <div className="text-xs text-white font-medium mt-0.5 leading-snug">{item.title}</div>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${item.status === 'Published' ? 'bg-emerald-500/15 text-emerald-400' : item.status === 'Scheduled' ? 'bg-blue-500/15 text-blue-400' : 'bg-neutral-700 text-neutral-400'}`}>
                {item.status}
              </span>
              <span className="text-[9px] text-neutral-500">Score <span className="text-emerald-400 font-bold">{item.score}</span></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const SHOWCASES = [
  {
    id: 'ai-workspace',
    label: 'AI Workspace',
    headline: 'Your Marketing Co-Pilot',
    description: 'Engage a full-stack AI agent that understands your brand, analyzes your past data, and collaborates with you in natural language to plan and execute campaigns.',
    cta: 'Explore AI Workspace',
    MockComponent: AiWorkspaceMock,
  },
  {
    id: 'crm',
    label: 'CRM',
    headline: 'Intelligent Contact Management',
    description: 'Move beyond static spreadsheets. Viptant CRM uses AI to score leads, predict deal velocity, surface at-risk opportunities, and automate follow-up sequences.',
    cta: 'Explore CRM',
    MockComponent: CrmMock,
  },
  {
    id: 'analytics',
    label: 'Analytics',
    headline: 'Insight Without the Analyst',
    description: 'Real-time dashboards that explain themselves. Viptant Analytics surfaces anomalies, generates natural language insights, and tells you what to do next.',
    cta: 'Explore Analytics',
    MockComponent: AnalyticsMock,
  },
  {
    id: 'content-studio',
    label: 'Content Studio',
    headline: 'Scale Content Without Scaling Headcount',
    description: 'Generate on-brand blog posts, email sequences, ad copy, and social content at 10× speed. Every asset comes with an SEO score, readability grade, and conversion prediction.',
    cta: 'Explore Content Studio',
    MockComponent: ContentMock,
  },
];

export function ShowcaseSection() {
  return (
    <section id="showcase" className="py-28 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-20">
          <FadeUp>
            <SectionLabel>Product Showcase</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Built for Real Marketing Work
            </GradientHeading>
          </FadeUp>
        </div>

        <div className="flex flex-col gap-28">
          {SHOWCASES.map((item, i) => {
            const Mock = item.MockComponent;
            const isEven = i % 2 === 0;
            return (
              <div
                key={item.id}
                className={`grid grid-cols-1 lg:grid-cols-2 gap-12 items-center ${!isEven ? 'lg:flex-row-reverse' : ''}`}
              >
                {/* Text side */}
                <FadeUp delay={0} className={!isEven ? 'lg:order-2' : ''}>
                  <div className="flex flex-col gap-5">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/8 bg-white/4 text-neutral-400 text-xs font-semibold w-fit">
                      {item.label}
                    </div>
                    <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
                      {item.headline}
                    </GradientHeading>
                    <p className="text-neutral-500 text-base leading-relaxed max-w-md">
                      {item.description}
                    </p>
                    <Link
                      href="/auth/register"
                      className="inline-flex items-center gap-2 text-sm font-semibold text-violet-400 hover:text-violet-300 transition-colors group w-fit"
                    >
                      {item.cta}
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </Link>
                  </div>
                </FadeUp>

                {/* Mock panel side */}
                <motion.div
                  initial={{ opacity: 0, x: isEven ? 40 : -40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: '-60px' }}
                  transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                  className={!isEven ? 'lg:order-1' : ''}
                >
                  <Mock />
                </motion.div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
