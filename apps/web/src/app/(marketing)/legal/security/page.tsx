'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, FileCheck, CheckCircle2, ChevronRight, Activity, Terminal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export default function SecurityPage() {
  const router = useRouter();

  const standards = [
    { title: 'SOC 2 Type II compliance', desc: 'Viptant undergoes annual independent audits covering security, availability, and processing integrity schemas.' },
    { title: 'Isolated database tables', desc: 'Each tenant vector vault database context runs within an isolated schema container to prevent cross-account leaks.' },
    { title: 'TLS 1.3 & AES-256 encryptions', desc: 'All telemetry logs and prompt outputs are encrypted in transit using TLS 1.3, and at rest using AES-256.' },
    { title: 'Hourly vulnerability scans', desc: 'Automated dependency checking and static code scanning run continuously in our build pipelines.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full border border-violet-500/20 bg-violet-500/5 text-violet-400 text-sm font-semibold mb-6">
              <Shield className="w-4 h-4" /> SOC 2 Type II Certified
            </div>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-1 mb-4">
              Security Framework
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              We design our agents, vaults, and APIs around enterprise security policies to safeguard corporate data pipelines.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Standards Grid Section ───────────────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6 text-left relative z-10">
        <div className="text-center mb-14">
          <FadeUp>
            <SectionLabel>Compliance & Infrastructure</SectionLabel>
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 text-white">Security Controls</h3>
          </FadeUp>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {standards.map((std, idx) => (
            <FadeUp 
              key={std.title} 
              delay={idx * 0.05}
              className="p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/20 transition-all flex items-start gap-4"
            >
              <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-violet-400 shrink-0">
                <Lock className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white mb-1.5">{std.title}</h4>
                <p className="text-neutral-500 text-xs sm:text-sm leading-relaxed">{std.desc}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ─── Bug Bounty / Disclosures Section ─────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30 text-left">
        <div className="max-w-3xl mx-auto px-6 space-y-6">
          <FadeUp>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Terminal className="w-5 h-5 text-indigo-400" /> Vulnerability Disclosures
            </h3>
            <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed">
              If you discover a security vulnerability in our vector pipelines, SDK client libraries, or dashboard systems, please submit a report immediately to <strong className="text-neutral-200">security@viptant.com</strong>.
            </p>
            <p className="text-xs text-neutral-500 leading-relaxed">
              We operate under a safe harbor policy. If findings are disclosed responsibly according to threat guidelines, we will work with you to resolve issues without legal actions.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Bottom CTA banner ──────────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50 text-center relative overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-violet-600/5 blur-[120px] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <FadeUp>
            <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-4">
              Need compliance documentation?
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Request our SOC 2 Type II audit logs, penetrations testing reports, or data storage certifications.
            </p>
            <div className="flex justify-center gap-3">
              <Button 
                variant="violet" 
                size="lg"
                onClick={() => router.push('/company/contact')}
                className="h-11 px-6 text-xs font-semibold"
              >
                Contact Security Desk <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}
