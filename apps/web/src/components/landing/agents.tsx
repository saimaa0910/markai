'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  PenTool, Search, Megaphone, FlaskConical, TrendingUp,
  BarChart2, HeadphonesIcon, GitBranch, CheckCircle
} from 'lucide-react';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

const AGENTS = [
  {
    icon: PenTool,
    name: 'Content Agent',
    tagline: 'Always-on creative',
    description: 'Generates blog posts, social captions, ad copy, email sequences, and landing pages — aligned to your brand voice.',
    benefits: ['Brand voice training', 'Multi-format output', 'Tone & style controls'],
    gradient: 'from-violet-600 to-purple-700',
    ring: 'ring-violet-500/20',
  },
  {
    icon: Search,
    name: 'SEO Agent',
    tagline: 'Organic growth engine',
    description: 'Performs keyword research, writes SEO-optimized content, builds topic clusters, and tracks ranking positions weekly.',
    benefits: ['Keyword clustering', 'SERP gap analysis', 'Auto meta tags'],
    gradient: 'from-blue-600 to-cyan-600',
    ring: 'ring-blue-500/20',
  },
  {
    icon: Megaphone,
    name: 'Campaign Agent',
    tagline: 'Launch, optimize, repeat',
    description: 'Plans, schedules, A/B tests, and auto-optimizes campaigns across email, social, and paid channels in real time.',
    benefits: ['Omnichannel reach', 'A/B auto-optimization', 'Smart scheduling'],
    gradient: 'from-orange-500 to-rose-600',
    ring: 'ring-orange-500/20',
  },
  {
    icon: FlaskConical,
    name: 'Research Agent',
    tagline: 'Competitive intelligence',
    description: 'Monitors competitors, scans industry news, extracts customer insights, and surfaces actionable market signals.',
    benefits: ['Competitor tracking', 'Sentiment analysis', 'Weekly briefings'],
    gradient: 'from-teal-500 to-emerald-600',
    ring: 'ring-teal-500/20',
  },
  {
    icon: TrendingUp,
    name: 'Sales Agent',
    tagline: 'Intelligent prospecting',
    description: 'Identifies high-intent leads, drafts personalized outreach, scores pipeline velocity, and books discovery calls.',
    benefits: ['Lead scoring', 'Personalized sequences', 'CRM auto-sync'],
    gradient: 'from-emerald-500 to-green-600',
    ring: 'ring-emerald-500/20',
  },
  {
    icon: BarChart2,
    name: 'Analytics Agent',
    tagline: 'Insights on autopilot',
    description: 'Builds automated performance reports, explains anomalies, forecasts revenue, and recommends budget reallocations.',
    benefits: ['Auto reporting', 'Anomaly detection', 'Revenue forecasting'],
    gradient: 'from-indigo-500 to-blue-700',
    ring: 'ring-indigo-500/20',
  },
  {
    icon: HeadphonesIcon,
    name: 'Support Agent',
    tagline: 'Customer experience AI',
    description: 'Handles marketing inquiries, routes hot leads to sales, resolves FAQ, and escalates complex issues to humans.',
    benefits: ['24/7 availability', 'Smart escalation', 'CRM integration'],
    gradient: 'from-pink-500 to-rose-600',
    ring: 'ring-pink-500/20',
  },
  {
    icon: GitBranch,
    name: 'Workflow Agent',
    tagline: 'Process automation',
    description: 'Connects apps, triggers actions based on events, and manages multi-step marketing processes without code.',
    benefits: ['No-code builder', 'Event triggers', '200+ integrations'],
    gradient: 'from-yellow-500 to-amber-600',
    ring: 'ring-yellow-500/20',
  },
];

function AgentCard({
  icon: Icon,
  name,
  tagline,
  description,
  benefits,
  gradient,
  ring,
  index,
}: (typeof AGENTS)[number] & { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
      className={`group relative flex flex-col p-6 rounded-2xl border border-white/6 bg-neutral-950/40 hover:border-white/12 transition-all duration-300 ring-1 ring-transparent hover:${ring}`}
    >
      {/* Top icon badge */}
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mb-5 shadow-lg`}>
        <Icon className="w-6 h-6 text-white" />
      </div>

      <div className="flex flex-col gap-2 flex-1">
        <div>
          <h3 className="text-base font-bold text-white">{name}</h3>
          <p className="text-xs font-medium text-neutral-500 mt-0.5">{tagline}</p>
        </div>
        <p className="text-sm text-neutral-500 leading-relaxed group-hover:text-neutral-400 transition-colors">
          {description}
        </p>
        <ul className="mt-3 space-y-1.5">
          {benefits.map((b) => (
            <li key={b} className="flex items-center gap-2 text-xs text-neutral-400">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
              {b}
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}

export function AgentsSection() {
  return (
    <section id="agents" className="py-28 relative overflow-hidden bg-neutral-950/30">
      {/* Grid dot overlay */}
      <div className="absolute inset-0 bg-grid-dots opacity-40 pointer-events-none" />
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/8 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/8 to-transparent" />

      <div className="max-w-7xl mx-auto px-6 relative">
        <div className="text-center mb-16">
          <FadeUp>
            <SectionLabel>AI Agent Roster</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Your AI Marketing Team
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="mt-5 text-neutral-500 text-lg max-w-2xl mx-auto leading-relaxed">
              Eight specialized AI agents that work autonomously and collaboratively — covering every corner of your marketing operation.
            </p>
          </FadeUp>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {AGENTS.map((agent, i) => (
            <AgentCard key={agent.name} {...agent} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
