'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

const INTEGRATIONS = [
  { name: 'Google', abbr: 'G', color: '#4285F4', bg: '#4285F410' },
  { name: 'Slack', abbr: '#', color: '#4A154B', bg: '#4A154B20' },
  { name: 'Meta', abbr: 'M', color: '#0082FB', bg: '#0082FB15' },
  { name: 'LinkedIn', abbr: 'in', color: '#0A66C2', bg: '#0A66C215' },
  { name: 'HubSpot', abbr: 'HS', color: '#FF7A59', bg: '#FF7A5915' },
  { name: 'Salesforce', abbr: 'SF', color: '#00A1E0', bg: '#00A1E015' },
  { name: 'OpenAI', abbr: 'AI', color: '#FFFFFF', bg: '#FFFFFF08' },
  { name: 'Gemini', abbr: 'Gm', color: '#8B5CF6', bg: '#8B5CF615' },
  { name: 'Claude', abbr: 'Cl', color: '#FF8C42', bg: '#FF8C4215' },
  { name: 'Zapier', abbr: 'Z', color: '#FF4A00', bg: '#FF4A0015' },
  { name: 'Microsoft', abbr: 'MS', color: '#00A4EF', bg: '#00A4EF15' },
];

function IntegrationChip({
  name,
  abbr,
  color,
  bg,
  index,
}: (typeof INTEGRATIONS)[number] & { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.3, delay: index * 0.04 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="flex flex-col items-center gap-2.5 p-4 rounded-2xl border border-white/6 bg-neutral-950/60 hover:border-white/14 cursor-pointer transition-colors group"
    >
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold border transition-all group-hover:scale-110"
        style={{ backgroundColor: bg, borderColor: `${color}30`, color }}
      >
        {abbr}
      </div>
      <span className="text-[11px] text-neutral-500 group-hover:text-neutral-300 transition-colors text-center font-medium">
        {name}
      </span>
    </motion.div>
  );
}

export function IntegrationsSection() {
  return (
    <section id="integrations" className="py-28 bg-neutral-950/30 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/8 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/8 to-transparent" />

      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-14">
          <FadeUp>
            <SectionLabel>200+ Integrations</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Connects to Your Entire Stack
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="mt-5 text-neutral-500 text-lg max-w-xl mx-auto leading-relaxed">
              Native two-way syncs with every major marketing, sales, and AI platform so nothing falls through the cracks.
            </p>
          </FadeUp>
        </div>

        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-11 gap-3">
          {INTEGRATIONS.map((item, i) => (
            <IntegrationChip key={item.name} {...item} index={i} />
          ))}
        </div>

        <FadeUp delay={0.3}>
          <p className="text-center text-sm text-neutral-600 mt-10">
            + 189 more integrations via Zapier and native API connectors.
          </p>
        </FadeUp>
      </div>
    </section>
  );
}
