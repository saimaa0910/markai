'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  Bot, Users, Megaphone, BarChart3, Zap, PenTool, Puzzle, Brain
} from 'lucide-react';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

const FEATURES = [
  {
    icon: Brain,
    title: 'AI Marketing',
    description: 'Multi-model AI gateway with Gemini, GPT-4o, and Claude routing intelligent campaigns and content at scale.',
    color: 'from-violet-600 to-indigo-600',
    glow: 'violet',
  },
  {
    icon: Users,
    title: 'CRM & Contacts',
    description: 'Unified pipeline from lead capture to deal close with AI-scored leads, activity timelines, and smart segmentation.',
    color: 'from-blue-600 to-cyan-600',
    glow: 'blue',
  },
  {
    icon: Megaphone,
    title: 'Campaigns',
    description: 'Omnichannel campaign orchestration across email, social, SMS, and paid ads from a single intelligent workspace.',
    color: 'from-orange-500 to-rose-500',
    glow: 'orange',
  },
  {
    icon: BarChart3,
    title: 'Analytics',
    description: 'Real-time dashboards, predictive cohort analysis, and AI-generated weekly performance insights and recommendations.',
    color: 'from-emerald-500 to-teal-600',
    glow: 'emerald',
  },
  {
    icon: Zap,
    title: 'Automation',
    description: 'Visual workflow builder with conditional logic, AI triggers, Zapier integrations, and built-in retry & monitoring.',
    color: 'from-yellow-500 to-orange-500',
    glow: 'yellow',
  },
  {
    icon: PenTool,
    title: 'Content Studio',
    description: 'AI-powered content creation: blog posts, social captions, email sequences, and ad copy — all brand-voice trained.',
    color: 'from-pink-500 to-rose-600',
    glow: 'pink',
  },
  {
    icon: Bot,
    title: 'AI Agents',
    description: 'Autonomous agents that plan, execute, and optimize campaigns overnight — your always-on marketing co-pilot.',
    color: 'from-violet-500 to-purple-700',
    glow: 'purple',
  },
  {
    icon: Puzzle,
    title: 'Integrations',
    description: '200+ native integrations including Google, Slack, HubSpot, Salesforce, Meta Ads, and LinkedIn Campaign Manager.',
    color: 'from-teal-500 to-cyan-600',
    glow: 'teal',
  },
];

function FeatureCard({
  icon: Icon,
  title,
  description,
  color,
  glow,
  index,
}: (typeof FEATURES)[number] & { index: number }) {
  const glowMap: Record<string, string> = {
    violet: 'rgba(139,92,246,0.15)',
    blue: 'rgba(59,130,246,0.15)',
    orange: 'rgba(249,115,22,0.15)',
    emerald: 'rgba(16,185,129,0.15)',
    yellow: 'rgba(234,179,8,0.15)',
    pink: 'rgba(236,72,153,0.15)',
    purple: 'rgba(168,85,247,0.15)',
    teal: 'rgba(20,184,166,0.15)',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.5, delay: index * 0.07, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="group relative p-6 rounded-2xl border border-white/6 bg-neutral-950/50 hover:border-white/12 cursor-pointer transition-all duration-300 overflow-hidden"
      style={{ '--glow': glowMap[glow] } as React.CSSProperties}
    >
      {/* Hover glow background */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"
        style={{ background: `radial-gradient(ellipse at 30% 30%, ${glowMap[glow]}, transparent 60%)` }}
      />

      <div className="relative flex flex-col gap-4">
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center shadow-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white mb-2 group-hover:text-white transition-colors">
            {title}
          </h3>
          <p className="text-sm text-neutral-500 leading-relaxed group-hover:text-neutral-400 transition-colors">
            {description}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export function PlatformSection() {
  return (
    <section id="platform" className="py-28 relative overflow-hidden">
      {/* Background accent */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-violet-600/4 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <FadeUp>
            <SectionLabel>The Full Platform</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Everything Marketing Teams Need.
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="mt-5 text-neutral-500 text-lg max-w-2xl mx-auto leading-relaxed">
              Stop stitching together 12 tools. Viptant unifies your entire marketing stack into one AI-orchestrated workspace.
            </p>
          </FadeUp>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((feature, i) => (
            <FeatureCard key={feature.title} {...feature} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
