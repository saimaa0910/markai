'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Info } from 'lucide-react';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

export default function CookiePolicyPage() {
  const cookies = [
    { type: 'Essential Session Cookies', purpose: 'Maintain user login sessions, workspace routes validation, and MFA auth tokens.', duration: 'Session-based' },
    { type: 'Telemetry Performance Cookies', purpose: 'Track dashboard query latency, search loads, and API playground latency logs.', duration: '30 days' },
    { type: 'Attribution Tracking Caches', purpose: 'Analyze referrers (e.g. Google Ads vs Organic blog) to attribute lead registration triggers.', duration: '90 days' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-12 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Legal Policy</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Cookie Policy
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm font-mono uppercase tracking-widest">
              Last Updated: July 14, 2026
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Cookie Classification Table ────────────────────────────────── */}
      <section className="py-20 max-w-4xl mx-auto px-6 text-left relative z-10">
        <FadeUp>
          <div className="flex items-center gap-2 mb-8">
            <Info className="w-5 h-5 text-violet-400" />
            <h3 className="text-lg font-bold text-white">How We Utilize Cookies</h3>
          </div>
          <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed mb-10">
            We use cookie records, server sessions, and local storage variables to authenticate developers, measure telemetry speeds, and map campaign touchpoints. We do not use third-party broker cookies for cross-context retargeting ads.
          </p>
        </FadeUp>

        <FadeUp delay={0.1} className="rounded-xl border border-white/6 overflow-hidden bg-black shadow-xl">
          <div className="grid grid-cols-3 p-4 bg-neutral-900/50 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-neutral-400 border-b border-white/5">
            <span>Cookie Type</span>
            <span>Technical Purpose</span>
            <span>Expiration</span>
          </div>

          {cookies.map((c) => (
            <div key={c.type} className="grid grid-cols-3 p-4 text-xs text-neutral-300 border-b border-white/5 last:border-0 hover:bg-white/2">
              <span className="font-semibold text-white">{c.type}</span>
              <span className="text-neutral-400 leading-relaxed pr-4">{c.purpose}</span>
              <span className="text-neutral-500 font-mono">{c.duration}</span>
            </div>
          ))}
        </FadeUp>

        {/* Browser Settings Guides */}
        <FadeUp delay={0.2} className="mt-16 space-y-4">
          <h3 className="text-base font-bold text-white">Managing Preferences</h3>
          <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed">
            You can configure your browser to block, filter, or notify you when cookies are set. Please note that blocking essential cookies will disable access to the Viptant organization dashboards and playground.
          </p>
        </FadeUp>
      </section>
    </div>
  );
}
