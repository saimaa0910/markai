'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { X, Check, Sparkles } from 'lucide-react';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

const TRADITIONAL = [
  '10+ disconnected tools to manage',
  'Multiple logins, multiple billing cycles',
  'Manual copy-pasting between platforms',
  'No AI — every task is manual work',
  'Data siloed in different dashboards',
  'Weeks to launch a campaign',
  'Guesswork-based optimization',
  'Large team required to scale',
];

const VIPTANT = [
  'One unified AI-native workspace',
  'Single login, one predictable price',
  'AI agents handle cross-platform ops',
  'Autonomous agents work 24/7 for you',
  'Unified data lake with real-time sync',
  'Launch campaigns in minutes with AI',
  'AI continuously learns and optimizes',
  'Scale to 10× with the same team',
];

export function ComparisonSection() {
  return (
    <section id="why-viptant" className="py-28">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <FadeUp>
            <SectionLabel>Why Viptant</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              The Old Way vs The Viptant Way
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="mt-5 text-neutral-500 text-lg max-w-xl mx-auto leading-relaxed">
              Modern marketing teams deserve a platform that matches their ambition — not a pile of disconnected tools.
            </p>
          </FadeUp>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Traditional side */}
          <FadeUp delay={0.1}>
            <div className="rounded-2xl border border-white/6 bg-neutral-950/60 p-8 h-full">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-9 h-9 rounded-xl bg-neutral-800 border border-white/8 flex items-center justify-center">
                  <X className="w-5 h-5 text-neutral-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Traditional Marketing Stack</h3>
                  <p className="text-xs text-neutral-500">The old way of doing things</p>
                </div>
              </div>
              <ul className="space-y-3.5">
                {TRADITIONAL.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-neutral-500">
                    <X className="w-4 h-4 text-rose-500/70 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </FadeUp>

          {/* Viptant side */}
          <FadeUp delay={0.2}>
            <div className="rounded-2xl border border-violet-500/20 bg-violet-500/4 p-8 h-full relative overflow-hidden glow-pulse">
              <div className="absolute top-0 right-0 w-48 h-48 bg-violet-600/8 rounded-full blur-3xl pointer-events-none" />
              <div className="flex items-center gap-3 mb-6">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Viptant AI Marketing OS</h3>
                  <p className="text-xs text-black-400 font-medium">The intelligent way forward</p>
                </div>
              </div>
              <ul className="space-y-3.5">
                {VIPTANT.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-neutral-300">
                    <Check className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </FadeUp>
        </div>
      </div>
    </section>
  );
}
