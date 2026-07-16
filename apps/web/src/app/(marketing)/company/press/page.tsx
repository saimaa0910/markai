'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Download, Calendar, Mail, FileText, Check, 
  Sparkles, CheckCircle2, ChevronRight, Archive, Info, Heart 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

interface Release {
  date: string;
  title: string;
  category: string;
  summary: string;
}

const RELEASES: Release[] = [
  { 
    date: 'July 14, 2026', 
    title: 'Viptant Achieves SOC 2 Type II Security Compliance Validation', 
    category: 'Security',
    summary: 'Viptant, the AI-Native Marketing Operating System, today announced it has successfully completed its Service Organization Control (SOC) 2 Type II audit, validating its security guardrails for enterprise customer data.'
  },
  { 
    date: 'April 28, 2026', 
    title: 'Viptant Raises $24M Series A to Expand Agentic Workflow Platforms', 
    category: 'Funding',
    summary: 'Led by Enterprise Capital Partners, the funding will accelerate AI research pipelines, vector database replication features, and developer SDK surfaces.'
  },
  { 
    date: 'November 12, 2025', 
    title: 'Viptant Launches Autonomous Multi-Agent Workspaces in Public Beta', 
    category: 'Product',
    summary: 'Introducing Content, SEO, CRM, and Campaign agents working collectively in a single system to automate campaign deployments across Google, Meta, and Salesforce.'
  },
  { 
    date: 'May 10, 2025', 
    title: 'Viptant Announces $6M Seed Round to Eliminate Marketing Friction', 
    category: 'Funding',
    summary: 'Viptant secures $6M seed investment to build the worlds first orchestrator specifically engineered for automated multi-channel campaign delivery.'
  },
];

const FACTS = [
  { label: 'Founded', value: '2024' },
  { label: 'Headquarters', value: 'Remote-First (Hubs in SF & NY)' },
  { label: 'Active Customers', value: '2,000+ marketing teams' },
  { label: 'Total Funding', value: '$30M (Seed + Series A)' },
  { label: 'Employee Count', value: '45 globally' },
  { label: 'Database Compliance', value: 'SOC 2 Type II, GDPR-ready' },
];

export default function PressPage() {
  const [downloadingAsset, setDownloadingAsset] = React.useState<string | null>(null);

  const triggerDownload = (name: string) => {
    setDownloadingAsset(name);
    setTimeout(() => setDownloadingAsset(null), 2500);
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Newsroom & Assets</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Press Room and Media Resources
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Explore recent announcements, download brand guidelines and vector assets, or get in touch with our public relations team.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Media Assets / Press Kit Downloads ───────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="text-center mb-14">
          <FadeUp>
            <SectionLabel>Downloads</SectionLabel>
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 text-white">Official Brand Kits</h3>
          </FadeUp>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { id: '1', title: 'Complete Press Kit', type: 'Full media pack', desc: 'Contains logo variations, founders headshots, product layouts, and corporate fact sheets.', size: 'ZIP, 42MB' },
            { id: '2', title: 'Brand Vector Assets', type: 'Logo & symbol files', desc: 'High-definition SVG, EPS, and PNG configurations of the Viptant mark for light/dark backdrops.', size: 'ZIP, 12MB' },
            { id: '3', title: 'Executive Bios & Statements', type: 'Founder backgrounds', desc: 'Detailed profiles and statements from Alex Rivera (CEO) and Dr. Sarah Chen (Chief Scientist).', size: 'PDF, 2.4MB' },
          ].map((asset, idx) => (
            <FadeUp 
              key={asset.id} 
              delay={idx * 0.05}
              className="p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/25 hover:bg-neutral-900/10 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-neutral-400 mb-5">
                  <Archive className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wider">{asset.type}</span>
                <h4 className="text-base font-bold text-white mt-1 mb-2.5">{asset.title}</h4>
                <p className="text-neutral-400 text-xs leading-relaxed mb-6">{asset.desc}</p>
              </div>

              <div className="flex items-center justify-between border-t border-white/5 pt-4 mt-auto">
                <span className="text-[10px] text-neutral-500 font-mono">{asset.size}</span>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => triggerDownload(asset.title)}
                  className="h-8 text-xs gap-1.5 px-3 border-white/8 text-neutral-300 hover:text-white"
                >
                  <Download className="w-3.5 h-3.5" /> Download
                </Button>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ─── Brand Guidelines Visual Gallery ─────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Guidelines */}
            <div className="lg:col-span-5">
              <FadeUp>
                <SectionLabel>Identity Guidelines</SectionLabel>
                <GradientHeading className="text-3xl font-extrabold tracking-tight mt-2 mb-6">
                  Applying the Viptant Brand
                </GradientHeading>
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-6">
                  We maintain a clean, high-contrast, technology-focused visual palette. When rendering our logomark in articles or coverage, please ensure:
                </p>

                <ul className="space-y-4">
                  {[
                    'Maintain a safety margin equal to 50% of the mark width.',
                    'Use the purple/white version on dark backdrops.',
                    'Use the black version on light backdrops.',
                    'Do not stretch, modify, skew, or apply drop-shadows to the mark.',
                  ].map((rule) => (
                    <li key={rule} className="flex items-start gap-2.5 text-xs text-neutral-300">
                      <CheckCircle2 className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
                      <span>{rule}</span>
                    </li>
                  ))}
                </ul>
              </FadeUp>
            </div>

            {/* Visual Swatches */}
            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-6 lg:pl-10">
              {/* Logo Mock Dark */}
              <FadeUp delay={0.1} className="p-8 rounded-xl border border-white/10 bg-black flex flex-col justify-between aspect-video relative">
                <span className="text-[10px] text-neutral-500 font-mono">Dark Logo Swatch</span>
                {/* Logo Placeholder */}
                <div className="flex items-center gap-2 self-center my-6">
                  <div className="w-6 h-6 rounded bg-violet-600 flex items-center justify-center text-xs font-bold text-white">V</div>
                  <span className="font-extrabold tracking-wider text-base text-white">Viptant</span>
                </div>
                <span className="text-[9px] text-neutral-500 text-right">BG: #000000 | Text: #FFFFFF</span>
              </FadeUp>

              {/* Logo Mock Light */}
              <FadeUp delay={0.2} className="p-8 rounded-xl border border-neutral-200 bg-white flex flex-col justify-between aspect-video relative">
                <span className="text-[10px] text-neutral-400 font-mono">Light Logo Swatch</span>
                {/* Logo Placeholder */}
                <div className="flex items-center gap-2 self-center my-6">
                  <div className="w-6 h-6 rounded bg-violet-600 flex items-center justify-center text-xs font-bold text-white">V</div>
                  <span className="font-extrabold tracking-wider text-base text-black">Viptant</span>
                </div>
                <span className="text-[9px] text-neutral-400 text-right">BG: #FFFFFF | Text: #000000</span>
              </FadeUp>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Company Facts Section ──────────────────────────────────────── */}
      <section className="py-20 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Quick Facts</SectionLabel>
              <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 text-white">Viptant at a Glance</h3>
            </FadeUp>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6 max-w-5xl mx-auto">
            {FACTS.map((fact, idx) => (
              <FadeUp 
                key={fact.label} 
                delay={idx * 0.04} 
                className="p-5 rounded-lg border border-white/5 bg-neutral-950/40 text-center"
              >
                <span className="text-2xl font-extrabold text-white block mb-1">{fact.value}</span>
                <span className="text-[10px] text-neutral-500 font-medium block uppercase tracking-wider">{fact.label}</span>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Press Releases Timeline ────────────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>News Releases</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Latest Announcements
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="space-y-8 relative before:absolute before:top-2 before:bottom-2 before:left-[17px] before:w-px before:bg-white/10">
            {RELEASES.map((rel, idx) => (
              <FadeUp key={rel.title} delay={idx * 0.05} className="flex gap-6 items-start relative group">
                {/* Visual Dot on Timeline */}
                <div className="w-9 h-9 rounded-full bg-neutral-950 border border-white/15 flex items-center justify-center shrink-0 z-10 group-hover:border-violet-500/40 transition-colors">
                  <FileText className="w-4 h-4 text-neutral-400 group-hover:text-violet-400 transition-colors" />
                </div>
                
                <div className="p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/20 hover:bg-neutral-900/10 flex-1 transition-all">
                  <div className="flex items-center gap-3 text-[10px] text-neutral-400 mb-2">
                    <span className="text-violet-400 font-bold uppercase tracking-wider">{rel.category}</span>
                    <span>·</span>
                    <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {rel.date}</span>
                  </div>
                  <h4 className="text-base font-bold text-white mb-2 leading-snug group-hover:text-violet-300 transition-colors">
                    {rel.title}
                  </h4>
                  <p className="text-neutral-400 text-xs leading-relaxed">{rel.summary}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Media PR Contact Box ────────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <FadeUp>
            <div className="w-12 h-12 rounded-full bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400 mx-auto mb-6">
              <Mail className="w-5 h-5" />
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-3">
              Media Contact
            </h3>
            <p className="text-neutral-400 text-xs sm:text-sm max-w-md mx-auto leading-relaxed mb-8">
              Are you a member of the press or an analyst seeking information or executive commentary? Get in touch directly.
            </p>

            <a 
              href="mailto:press@viptant.com"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors text-xs font-semibold text-white cursor-pointer"
            >
              Email press@viptant.com <ChevronRight className="w-3.5 h-3.5" />
            </a>

            <div className="p-3 bg-neutral-950/60 border border-white/5 rounded-lg text-[10px] text-neutral-500 max-w-xs mx-auto mt-6">
              PR Pledge: <strong className="text-neutral-300">Responds in &lt;4 hours</strong> for verified press.
            </div>
          </FadeUp>
        </div>
      </section>

      {/* Toast Notification for assets downloading */}
      <AnimatePresence>
        {downloadingAsset && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 right-6 z-50 p-4 rounded-xl border border-violet-500/30 bg-neutral-950 shadow-2xl max-w-sm flex items-start gap-3"
          >
            <div className="w-8 h-8 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400 shrink-0">
              <Check className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">Download Started</h4>
              <p className="text-[10px] text-neutral-400 mt-0.5 leading-relaxed">
                Your browser download has started for <strong className="text-violet-300">{downloadingAsset}</strong>.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
