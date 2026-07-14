'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Lightbulb, Brain, PenTool, Megaphone, Globe, BarChart3, Rocket } from 'lucide-react';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

const STEPS = [
  { icon: Lightbulb, label: 'Idea', desc: 'You describe the goal', color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/20' },
  { icon: Brain, label: 'AI Planning', desc: 'Agent builds the strategy', color: 'text-violet-400', bg: 'bg-violet-400/10 border-violet-400/20' },
  { icon: PenTool, label: 'Content', desc: 'Assets generated at scale', color: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/20' },
  { icon: Megaphone, label: 'Campaign', desc: 'Multi-channel orchestration', color: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/20' },
  { icon: Globe, label: 'Publish', desc: 'Live across all channels', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/20' },
  { icon: BarChart3, label: 'Analyze', desc: 'Real-time performance data', color: 'text-cyan-400', bg: 'bg-cyan-400/10 border-cyan-400/20' },
  { icon: Rocket, label: 'Optimize', desc: 'AI improves continuously', color: 'text-pink-400', bg: 'bg-pink-400/10 border-pink-400/20' },
];

export function WorkflowSection() {
  return (
    <section id="workflow" className="py-28">
      <div className="max-w-5xl mx-auto px-6">
        <div className="text-center mb-16">
          <FadeUp>
            <SectionLabel>Intelligent Workflow</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              From Idea to Impact
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="mt-5 text-neutral-500 text-lg max-w-xl mx-auto leading-relaxed">
              Viptant's AI agents handle the entire marketing lifecycle — from strategy to optimization — without manual handoffs.
            </p>
          </FadeUp>
        </div>

        {/* Vertical flow chart */}
        <div className="flex flex-col items-center gap-0">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <React.Fragment key={step.label}>
                <motion.div
                  initial={{ opacity: 0, scale: 0.85 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true, margin: '-30px' }}
                  transition={{ duration: 0.4, delay: i * 0.1 }}
                  className="flex items-center gap-6 w-full max-w-md"
                >
                  {/* Icon node */}
                  <div className={`w-14 h-14 rounded-2xl border flex items-center justify-center flex-shrink-0 ${step.bg}`}>
                    <Icon className={`w-6 h-6 ${step.color}`} />
                  </div>

                  {/* Label */}
                  <div>
                    <div className="text-base font-bold text-white">{step.label}</div>
                    <div className="text-sm text-neutral-500 mt-0.5">{step.desc}</div>
                  </div>

                  {/* Step number */}
                  <div className="ml-auto text-2xl font-black text-neutral-800 select-none">
                    {String(i + 1).padStart(2, '0')}
                  </div>
                </motion.div>

                {/* Connector line */}
                {i < STEPS.length - 1 && (
                  <motion.div
                    initial={{ scaleY: 0 }}
                    whileInView={{ scaleY: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.3, delay: i * 0.1 + 0.3 }}
                    className="w-px h-8 bg-gradient-to-b from-white/12 to-white/4 origin-top"
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </section>
  );
}
