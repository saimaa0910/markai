'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Github, MessageSquare, Terminal, Users, Sparkles, 
  ExternalLink, ChevronRight, Star, GitFork, AlertCircle 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

interface CommunityChannel {
  name: string;
  desc: string;
  icon: any;
  actionText: string;
  href: string;
  color: string;
}

const CHANNELS: CommunityChannel[] = [
  {
    name: 'Discord Server',
    desc: 'Join 10,000+ developers, marketers, and AI researchers swapping prompt blueprints and automation flows.',
    icon: MessageSquare,
    actionText: 'Join Discord Server',
    href: 'https://discord.gg/viptant',
    color: 'from-indigo-600/20 to-violet-600/20 border-indigo-500/20 text-indigo-400',
  },
  {
    name: 'GitHub Portal',
    desc: 'Contribute to our open-source REST SDKs packages, report schema bugs, or review client bindings.',
    icon: Github,
    actionText: 'Explore GitHub Repos',
    href: 'https://github.com/viptant',
    color: 'from-neutral-800 to-neutral-900 border-white/5 text-neutral-400',
  },
  {
    name: 'Community Forum',
    desc: 'Read in-depth threads on custom vector database syncing patterns, rate-limit settings, and brand voice PDF optimization.',
    icon: Terminal,
    actionText: 'Browse Community Forum',
    href: '#',
    color: 'from-blue-600/20 to-cyan-600/20 border-blue-500/20 text-blue-400',
  },
];

export default function CommunityPage() {
  const [copiedKey, setCopiedKey] = React.useState<string | null>(null);

  const triggerCopy = (key: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Developer Community</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Connect with Viptant Builders
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Swaps prompt templates, report issues, audit plugins, and build agentic workflows collectively with enterprise developers globally.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Grid List of Channels ───────────────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6 text-left relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
          {CHANNELS.map((ch, idx) => {
            const Icon = ch.icon;
            return (
              <FadeUp 
                key={ch.name} 
                delay={idx * 0.05}
                className="group p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/25 hover:bg-neutral-900/10 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-neutral-400 mb-5 group-hover:text-violet-400 group-hover:border-violet-500/20 transition-all">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-bold text-white mb-2 leading-snug group-hover:text-violet-300 transition-colors">
                    {ch.name}
                  </h4>
                  <p className="text-neutral-400 text-xs leading-relaxed mb-6">{ch.desc}</p>
                </div>

                <a 
                  href={ch.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-1.5 w-full py-2.5 rounded bg-neutral-900 border border-white/8 hover:bg-neutral-850 hover:text-white transition-all text-xs font-semibold text-neutral-300 cursor-pointer"
                >
                  {ch.actionText} <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </FadeUp>
            );
          })}
        </div>

        {/* ─── GitHub Stats Widget ────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center max-w-5xl mx-auto border-t border-white/5 pt-20">
          <div className="lg:col-span-5 space-y-6">
            <FadeUp>
              <SectionLabel>Open Source</SectionLabel>
              <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 text-white">
                GitHub Repository
              </h3>
              <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed">
                Viptant SDKs packages libraries are 100% open-source on GitHub. We welcome package PR contribution hooks and documentation fixes.
              </p>
            </FadeUp>

            {/* Mock GitHub stats */}
            <FadeUp delay={0.1} className="grid grid-cols-3 gap-4 border-t border-white/5 pt-6 mt-6">
              <div className="flex flex-col">
                <span className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-1">
                  <Star className="w-4 h-4 text-amber-500 fill-amber-500" /> 1,284
                </span>
                <span className="text-[9px] text-neutral-500 uppercase block font-semibold mt-1">Stars</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-1">
                  <GitFork className="w-4 h-4 text-violet-400" /> 142
                </span>
                <span className="text-[9px] text-neutral-500 uppercase block font-semibold mt-1">Forks</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-1">
                  <Users className="w-4 h-4 text-indigo-400" /> 48
                </span>
                <span className="text-[9px] text-neutral-500 uppercase block font-semibold mt-1">Contributors</span>
              </div>
            </FadeUp>
          </div>

          <div className="lg:col-span-7">
            <FadeUp delay={0.2} className="relative rounded-2xl border border-white/10 bg-neutral-950/80 p-5 glass overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3.5 mb-4">
                <div className="flex items-center gap-2">
                  <Github className="w-4 h-4 text-neutral-400" />
                  <span className="text-xs font-mono text-neutral-300">viptant-sdk-node</span>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-[9px] text-emerald-400 font-mono font-semibold">BUILD PASSING</span>
              </div>

              {/* Install Code */}
              <div className="p-3.5 rounded bg-neutral-900 border border-white/5 text-[10px] font-mono text-neutral-400 mb-4 flex items-center justify-between">
                <span>npm install @viptant/node</span>
                <button 
                  onClick={() => triggerCopy('npm install @viptant/node')}
                  className="text-neutral-500 hover:text-white transition-colors cursor-pointer text-[9px]"
                >
                  {copiedKey === 'npm install @viptant/node' ? 'Copied!' : 'Copy'}
                </button>
              </div>

              <div className="space-y-2.5 text-[9px] font-mono text-neutral-500 border-t border-white/5 pt-4">
                <div className="flex items-center gap-1.5"><AlertCircle className="w-3.5 h-3.5 text-violet-400" /> Latest Release: v1.2.4 (2 days ago)</div>
                <div className="flex items-center gap-1.5"><AlertCircle className="w-3.5 h-3.5 text-violet-400" /> Verified: Node.js v18 & v20 compliance</div>
              </div>
            </FadeUp>
          </div>
        </div>
      </section>
    </div>
  );
}
