'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, CheckCircle2, AlertTriangle, ShieldCheck, 
  Clock, Calendar, Sparkles, ChevronRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

interface ComponentStatus {
  name: string;
  uptime: string;
  latency: string;
  status: 'operational' | 'degraded' | 'maintenance';
}

const COMPONENTS: ComponentStatus[] = [
  { name: 'Core API Server', uptime: '99.99%', latency: '128ms', status: 'operational' },
  { name: 'AI Gateway Proxy', uptime: '99.98%', latency: '14ms', status: 'operational' },
  { name: 'Vector DB Pipelines', uptime: '100.0%', latency: '42ms', status: 'operational' },
  { name: 'Web Application Client', uptime: '99.97%', latency: '115ms', status: 'operational' },
  { name: 'Document Cloud Storage', uptime: '100.0%', latency: '65ms', status: 'operational' },
];

const INCIDENTS = [
  {
    date: 'July 14, 2026',
    title: 'Scheduled Vector Database Replication Maintenance',
    status: 'Resolved',
    desc: 'Our vector query cluster underwent a scheduled maintenance sprint to double indexes replication slots. The platform was offline for exactly 11 minutes. All operations completed successfully.',
  },
  {
    date: 'June 10, 2026',
    title: 'AI Gateway Latency Degradation (GPT-4o routing)',
    status: 'Resolved',
    desc: 'An upstream OpenAI route outage caused connection delays of up to 3s. The gateway auto-routed active prompts to Claude models within 2 seconds. The issue resolved upon OpenAI recovery.',
  },
];

export default function StatusPage() {
  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Header Hero operational banner ───────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>System Status</SectionLabel>
          </FadeUp>

          {/* Operational Status Display */}
          <FadeUp delay={0.1}>
            <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-sm font-semibold mb-6">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping shrink-0" />
              All Systems Operational
            </div>
          </FadeUp>

          <FadeUp delay={0.2}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-1 mb-4">
              Service Health Dashboard
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.3}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Monitor real-time system metrics, component uptime logs, incident updates, and scheduled maintenance schedules.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Real-Time Component Grid ────────────────────────────────────── */}
      <section className="py-20 max-w-4xl mx-auto px-6 text-left relative z-10">
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-violet-400" /> Component Metrics
          </h3>
          <span className="text-[10px] text-neutral-500 font-mono">UPDATED: REAL-TIME (10s sync)</span>
        </div>

        <div className="space-y-6">
          {COMPONENTS.map((comp, idx) => (
            <FadeUp 
              key={comp.name} 
              delay={idx * 0.04}
              className="p-5 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-white/10 transition-all flex flex-col gap-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white">{comp.name}</h4>
                  <span className="text-[10px] text-neutral-500 font-mono">Response time: {comp.latency}</span>
                </div>

                <div className="flex items-center gap-3 text-right">
                  <div>
                    <span className="text-xs font-bold text-white block">{comp.uptime}</span>
                    <span className="text-[9px] text-neutral-500 block uppercase">90-day uptime</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-bold text-emerald-400 font-mono">
                    OPERATIONAL
                  </span>
                </div>
              </div>

              {/* Decorative Uptime 90-day Bar Grid */}
              <div className="flex items-center gap-1">
                {Array.from({ length: 42 }).map((_, i) => (
                  <div 
                    key={i} 
                    className={`h-4 flex-1 rounded-xs transition-colors ${
                      i === 12 && comp.name.includes('Gateway') ? 'bg-amber-500/40' :
                      i === 38 && comp.name.includes('Client') ? 'bg-amber-500/40' : 'bg-emerald-500/60'
                    }`}
                    title="Uptime: 100.0%"
                  />
                ))}
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ─── Incidents Timeline Section ─────────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30 text-left">
        <div className="max-w-3xl mx-auto px-6">
          <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-8">
            <Clock className="w-5 h-5 text-indigo-400" /> Incident History
          </h3>

          <div className="space-y-8 relative before:absolute before:top-2 before:bottom-2 before:left-[17px] before:w-px before:bg-white/10">
            {INCIDENTS.map((inc, idx) => (
              <FadeUp key={inc.title} delay={idx * 0.05} className="flex gap-6 items-start relative group">
                
                {/* Timeline icon */}
                <div className="w-9 h-9 rounded-full bg-neutral-950 border border-white/15 flex items-center justify-center shrink-0 z-10">
                  <Calendar className="w-4 h-4 text-neutral-500" />
                </div>

                <div className="p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/20 hover:bg-neutral-900/10 flex-1 transition-all">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] text-neutral-400 font-mono">{inc.date}</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-bold text-emerald-400">
                      {inc.status.toUpperCase()}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-white mb-2 leading-snug">
                    {inc.title}
                  </h4>

                  <p className="text-neutral-500 text-[11px] sm:text-xs leading-relaxed">
                    {inc.desc}
                  </p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
