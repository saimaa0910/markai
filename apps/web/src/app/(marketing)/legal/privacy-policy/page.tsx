'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Shield, Eye, Lock, FileText, ArrowRight } from 'lucide-react';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

export default function PrivacyPolicyPage() {
  const sections = [
    {
      id: 'information-collect',
      title: '1. Information We Collect',
      desc: 'We collect information directly provided by you during registration, details synchronizing from your linked CRM databases, and telemetry logs reflecting user browser interactions. Vector vault document content is parsed in memory and encrypted at rest.',
    },
    {
      id: 'how-use-data',
      title: '2. How We Use Data',
      desc: 'Collected data is used solely to configure AI model behaviors, map multi-channel attribution paths, deliver lead enrichment reports, and optimize campaign delivery queues. We do not use customer data to train foundation model systems.',
    },
    {
      id: 'sharing-policy',
      title: '3. Sharing and Disclosing',
      desc: 'Viptant does not sell or distribute database contacts. We exchange context tokens with trusted AI infrastructure providers (Google, Anthropic, OpenAI) to generate content, governed by enterprise safety agreements.',
    },
    {
      id: 'data-retention',
      title: '4. Data Retentions',
      desc: 'Telemetry log caches are cleared after 90 days. Workspace vector databases are maintained for the lifetime of your organization account, and fully deleted within 30 days of subscription termination.',
    },
    {
      id: 'contact-info',
      title: '5. Contact Operations',
      desc: 'For inquiries regarding data storage boundaries, compliance audits, or requests for system logs, contact our privacy desk at privacy@viptant.com.',
    },
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
              Privacy Policy
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm font-mono uppercase tracking-widest">
              Last Updated: July 14, 2026
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Core Document Layout ────────────────────────────────────────── */}
      <section className="py-20 max-w-5xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 text-left relative z-10">
        {/* Table of Contents Column (col-span-4) */}
        <div className="lg:col-span-4 hidden lg:block">
          <div className="sticky top-28 space-y-4">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block mb-4">Document Outline</span>
            <ul className="space-y-3 text-xs">
              {sections.map((s) => (
                <li key={s.id}>
                  <a href={`#${s.id}`} className="text-neutral-400 hover:text-white transition-colors">
                    {s.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Text Details Column (col-span-8) */}
        <div className="lg:col-span-8 space-y-12 leading-relaxed">
          {sections.map((s, idx) => (
            <div id={s.id} key={s.id} className="scroll-mt-28">
              <FadeUp delay={idx * 0.04}>
                <h3 className="text-lg font-bold text-white mb-4">{s.title}</h3>
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-4">{s.desc}</p>
                <div className="h-px bg-white/5 mt-8" />
              </FadeUp>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
