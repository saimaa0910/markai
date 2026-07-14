'use client';

import * as React from 'react';
import { FadeUp, SectionLabel } from './primitives';

const LOGOS = [
  { name: 'Salesforce', abbr: 'SF', color: '#00A1E0' },
  { name: 'HubSpot', abbr: 'HS', color: '#FF7A59' },
  { name: 'LinkedIn', abbr: 'in', color: '#0A66C2' },
  { name: 'Google', abbr: 'G', color: '#4285F4' },
  { name: 'Meta', abbr: 'M', color: '#0082FB' },
  { name: 'Slack', abbr: '#', color: '#4A154B' },
  { name: 'Zapier', abbr: 'Z', color: '#FF4A00' },
  { name: 'Microsoft', abbr: 'MS', color: '#00A4EF' },
  { name: 'Stripe', abbr: 'S', color: '#635BFF' },
  { name: 'Notion', abbr: 'N', color: '#FFFFFF' },
  { name: 'Figma', abbr: 'F', color: '#F24E1E' },
  { name: 'Intercom', abbr: 'IC', color: '#2196F3' },
];

function LogoItem({ name, abbr, color }: { name: string; abbr: string; color: string }) {
  return (
    <div className="flex items-center gap-2.5 px-5 py-3 rounded-xl bg-neutral-900/60 border border-white/5 select-none hover:border-white/10 transition-colors cursor-default">
      <div
        className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs text-white"
        style={{ backgroundColor: `${color}25`, border: `1px solid ${color}40`, color }}
      >
        {abbr}
      </div>
      <span className="text-sm font-medium text-neutral-400 whitespace-nowrap">{name}</span>
    </div>
  );
}

export function TrustSection() {
  // Duplicate for seamless marquee loop
  const items = [...LOGOS, ...LOGOS];

  return (
    <section className="py-16 border-y border-white/5 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 mb-8 text-center">
        <FadeUp>
          <SectionLabel>Trusted By Marketing Leaders</SectionLabel>
          <p className="text-neutral-500 text-sm">
            Integrates natively with the tools your team already uses.
          </p>
        </FadeUp>
      </div>

      {/* Marquee container */}
      <div className="marquee-track relative overflow-hidden w-full">
        {/* Fade edges */}
        <div className="absolute left-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-r from-black to-transparent pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-l from-black to-transparent pointer-events-none" />

        <div className="animate-marquee flex gap-4 w-max">
          {items.map((logo, i) => (
            <LogoItem key={`${logo.name}-${i}`} {...logo} />
          ))}
        </div>
      </div>
    </section>
  );
}
