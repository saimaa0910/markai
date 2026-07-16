'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { 
  Rss, Calendar, ArrowUpRight, Sparkles, Check, CheckCircle2, ChevronRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

interface ChangeLogEntry {
  version: string;
  date: string;
  title: string;
  summary: string;
  notes: { category: 'added' | 'improved' | 'fixed' | 'security'; items: string[] }[];
}

const CHANGELOG: ChangeLogEntry[] = [
  {
    version: 'v2.4.0',
    date: 'July 14, 2026',
    title: 'Model Routing & SOC 2 Compliance Validation',
    summary: 'Introducing dynamic model routing metrics in the AI Gateway, optimizing performance costs by routing reasoning checks dynamically across Gemini and Claude. This release also marks our official SOC 2 compliance verification.',
    notes: [
      { category: 'added', items: ['Dynamic schema fallback checks inside HTTP proxy gateway.', 'Audit logging trails page in Dashboard security panel.'] },
      { category: 'improved', items: ['Reduced vector search latency overheads by 18% via metadata indexing caching.', 'Next.js rendering load speeds for static subpages.'] },
      { category: 'security', items: ['Tenant database isolation validation reports generated automatically.'] },
    ],
  },
  {
    version: 'v2.3.1',
    date: 'June 18, 2026',
    title: 'Semantic De-duplication for CRM Pipelines',
    summary: 'A performance fix update to clean CRM databases by analyzing incoming leads using semantic logic instead of strict exact string matches.',
    notes: [
      { category: 'improved', items: ['CRM pipeline data enrichment scraping speed increased by 30%.'] },
      { category: 'fixed', items: ['Resolved retry timeouts occurring during Slack notification alerts dispatch.', 'Fixed metadata hydration glitches on the campaign preview calendar.'] },
    ],
  },
  {
    version: 'v2.2.0',
    date: 'May 02, 2026',
    title: 'Campaign Autopilot Release',
    summary: 'Our major release adding fully autonomous execution states for AI Agents. Marketers can now toggle "Autopilot" to permit agents to directly publish campaigns to LinkedIn and Google APIs.',
    notes: [
      { category: 'added', items: ['Autopilot toggle control options per channel workspace.', 'Budget safety throttling parameters to throttle cost metrics automatically.'] },
      { category: 'improved', items: ['Added Axios retry adapters to REST SDK clients package registries.'] },
    ],
  },
];

export default function ChangelogPage() {
  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Changelog</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Platform Release History
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Track new integrations, feature rollouts, API updates, performance metrics, and compliance logs weekly.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Split Grid: Timeline vs Newsletter ─────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 text-left relative z-10">
        
        {/* Timeline (col-span-8) */}
        <div className="lg:col-span-8 space-y-12 relative before:absolute before:top-2 before:bottom-2 before:left-[17px] before:w-px before:bg-white/10">
          {CHANGELOG.map((entry, idx) => (
            <FadeUp key={entry.version} delay={idx * 0.05} className="flex gap-6 items-start relative group">
              
              {/* Timeline Indicator Badge */}
              <div className="w-9 h-9 rounded-full bg-neutral-950 border border-white/15 flex items-center justify-center shrink-0 z-10 font-mono text-[10px] font-bold text-violet-400 group-hover:border-violet-500/40 transition-colors">
                {entry.version.slice(1, 4)}
              </div>

              {/* Release Card */}
              <div className="p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/20 hover:bg-neutral-900/10 flex-1 transition-all">
                <div className="flex items-center gap-3 text-[10px] text-neutral-400 mb-3">
                  <span className="px-2 py-0.5 rounded bg-violet-600/10 border border-violet-500/20 font-bold text-violet-400 font-mono">{entry.version}</span>
                  <span>·</span>
                  <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5 text-neutral-500" /> {entry.date}</span>
                </div>

                <h4 className="text-lg font-bold text-white mb-2 leading-snug">
                  {entry.title}
                </h4>

                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-6">
                  {entry.summary}
                </p>

                {/* Release details list */}
                <div className="space-y-4 pt-4 border-t border-white/5 text-xs">
                  {entry.notes.map((note) => (
                    <div key={note.category} className="space-y-1.5">
                      <span className={`text-[9px] font-bold uppercase tracking-wider block ${
                        note.category === 'added' ? 'text-emerald-400' :
                        note.category === 'improved' ? 'text-violet-400' :
                        note.category === 'security' ? 'text-blue-400' : 'text-amber-400'
                      }`}>
                        {note.category}
                      </span>
                      <ul className="space-y-1.5 pl-4 list-disc text-neutral-400 leading-relaxed text-[11px] sm:text-xs">
                        {note.items.map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </FadeUp>
          ))}
        </div>

        {/* Subscribe Sidebar (col-span-4) */}
        <div className="lg:col-span-4">
          <div className="sticky top-28 p-6 rounded-xl border border-white/6 bg-neutral-950/40 space-y-5 glass">
            <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-violet-400">
              <Rss className="w-5 h-5" />
            </div>

            <h3 className="text-sm font-bold text-white">Subscribe to Updates</h3>
            <p className="text-[11px] sm:text-xs text-neutral-400 leading-relaxed">
              Add our developer changelog feed to your RSS client, or receive release notifications directly on Slack.
            </p>

            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full h-9 text-[10px] font-semibold border-white/8 text-neutral-300 hover:text-white"
                onClick={() => window.open('/feed.xml', '_blank')}
              >
                Copy RSS Feed URL <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
