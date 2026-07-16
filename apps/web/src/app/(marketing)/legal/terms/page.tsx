'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Scale, ShieldCheck, HelpCircle } from 'lucide-react';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

export default function TermsOfServicePage() {
  const sections = [
    {
      id: 'account-terms',
      title: '1. Account Agreements',
      desc: 'Users must register account credentials truthfully. Sharing passwords or API tokens outside of organization boundaries is strictly prohibited. You are responsible for all trigger actions performed using your credentials.',
    },
    {
      id: 'agent-conduct',
      title: '2. Agent Usage Rules',
      desc: 'You agree not to configure Viptant agents to output hate speech, generate scam credentials, trigger spam campaigns exceeding platform rates, or violate local advertising laws. We reserve the right to throttle active pipelines if abuse is detected.',
    },
    {
      id: 'intellectual-property',
      title: '3. Intellectual Properties',
      desc: 'Viptant claims no ownership over generated content drafts, layouts, or data tables created by your agents. The models configuration, prompt histories, and vectors database belong entirely to your organization.',
    },
    {
      id: 'disclaimers',
      title: '4. Warranties and Disclaimers',
      desc: 'Our services are provided "as is." AI generations are probabilistic. While our safety rails check content validity, we make no guarantees regarding accuracy, click-through conversions, or search engine ranking gains.',
    },
    {
      id: 'liabilities',
      title: '5. Limitations of Liabilities',
      desc: 'In no event shall Viptant be liable for pipeline down-times, model cost drifts, or ad account suspension claims resulting from automated campaign publications. Liability is capped at the total subscription fees paid.',
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
              Terms of Service
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
