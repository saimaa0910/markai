'use client';

import * as React from 'react';
import { FadeUp, SectionLabel, GradientHeading, StatCard } from './primitives';

const STORIES = [
  {
    company: 'ScaleHQ',
    industry: 'B2B SaaS',
    logo: 'SH',
    logoColor: '#8B5CF6',
    quote: 'Viptant replaced 7 tools and reduced our campaign launch time from 3 weeks to 4 hours. Our pipeline grew 3× in Q3.',
    author: 'Maya Patel',
    role: 'VP of Marketing',
    metrics: [
      { value: '3×', label: 'Pipeline growth' },
      { value: '94%', label: 'Time saved on copy' },
      { value: '$2.1M', label: 'Revenue attributed' },
    ],
  },
  {
    company: 'Nexara Health',
    industry: 'HealthTech',
    logo: 'NH',
    logoColor: '#10B981',
    quote: 'The AI agents generated 400+ pieces of compliant healthcare content in a month. Our SEO traffic grew 220% in 90 days.',
    author: 'Dr. James Osei',
    role: 'Chief Growth Officer',
    metrics: [
      { value: '220%', label: 'SEO traffic growth' },
      { value: '400+', label: 'Compliant assets/month' },
      { value: '18×', label: 'Content output increase' },
    ],
  },
  {
    company: 'TradeBridge',
    industry: 'FinTech',
    logo: 'TB',
    logoColor: '#F59E0B',
    quote: 'We onboarded Viptant during a Series B push. The campaign AI alone generated 1,800 qualified leads in 6 weeks.',
    author: 'Sofia Chen',
    role: 'Head of Demand Generation',
    metrics: [
      { value: '1,800', label: 'Qualified leads, 6 weeks' },
      { value: '4.2×', label: 'ROAS improvement' },
      { value: '60%', label: 'CAC reduction' },
    ],
  },
];

function StoryCard({ company, industry, logo, logoColor, quote, author, role, metrics }: (typeof STORIES)[number]) {
  return (
    <div className="flex flex-col p-7 rounded-2xl border border-white/6 bg-neutral-950/50 hover:border-white/12 transition-colors h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm text-white"
            style={{ backgroundColor: `${logoColor}25`, border: `1px solid ${logoColor}40`, color: logoColor }}
          >
            {logo}
          </div>
          <div>
            <div className="text-sm font-bold text-white">{company}</div>
            <div className="text-xs text-neutral-500">{industry}</div>
          </div>
        </div>
        <div className="text-2xl text-neutral-600 font-serif leading-none">"</div>
      </div>

      {/* Quote */}
      <blockquote className="text-sm text-neutral-300 leading-relaxed flex-1 mb-5">
        {quote}
      </blockquote>

      {/* Author */}
      <div className="flex items-center gap-2 mb-6 pb-5 border-b border-white/5">
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs text-white"
          style={{ backgroundColor: `${logoColor}30`, color: logoColor }}
        >
          {author[0]}
        </div>
        <div>
          <div className="text-xs font-semibold text-white">{author}</div>
          <div className="text-[10px] text-neutral-500">{role}</div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3">
        {metrics.map((m) => (
          <div key={m.label} className="flex flex-col gap-0.5">
            <span className="text-lg font-extrabold text-white">{m.value}</span>
            <span className="text-[10px] text-neutral-500">{m.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function StoriesSection() {
  return (
    <section id="stories" className="py-28 bg-neutral-950/30 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/8 to-transparent" />

      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <FadeUp>
            <SectionLabel>Customer Stories</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Results That Speak for Themselves
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="mt-5 text-neutral-500 text-lg max-w-xl mx-auto">
              Viptant customers across every industry are seeing transformative results within their first 90 days.
            </p>
          </FadeUp>
        </div>

        {/* Aggregate stats */}
        <FadeUp delay={0.2}>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-16 p-8 rounded-2xl border border-white/5 bg-neutral-950/40">
            <StatCard value="2,000" suffix="+" label="Companies onboarded" />
            <StatCard value="94" suffix="%" label="Customer satisfaction score" />
            <StatCard value="10" suffix="×" label="Average content output increase" />
            <StatCard value="$180" suffix="M+" label="Pipeline influenced" />
          </div>
        </FadeUp>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {STORIES.map((story, i) => (
            <FadeUp key={story.company} delay={i * 0.1}>
              <StoryCard {...story} />
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}
