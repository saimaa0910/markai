'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  TrendingUp,
  Users,
  MessageSquare,
  Sparkles,
  Send,
  ChevronRight,
  ArrowUpRight,
} from 'lucide-react';

// ─── Small sparkle mini-chart bar ────────────────────────────────────────────
function MiniBar({ height, active }: { height: number; active?: boolean }) {
  return (
    <div
      className={`w-4 rounded-sm transition-all duration-300 origin-bottom ${active ? 'bg-violet-500' : 'bg-neutral-700'}`}
      style={{ height }}
    />
  );
}

// ─── KPI metric card ─────────────────────────────────────────────────────────
function KpiCard({
  label,
  value,
  change,
  positive = true,
}: {
  label: string;
  value: string;
  change: string;
  positive?: boolean;
}) {
  return (
    <div className="p-3 rounded-xl bg-neutral-900/80 border border-white/5 flex flex-col gap-1.5">
      <span className="text-[10px] text-neutral-500 font-medium uppercase tracking-wider">{label}</span>
      <span className="text-lg font-bold text-white">{value}</span>
      <span className={`text-[10px] font-semibold flex items-center gap-0.5 ${positive ? 'text-emerald-400' : 'text-rose-400'}`}>
        <TrendingUp className="w-3 h-3" />
        {change}
      </span>
    </div>
  );
}

// ─── Mini AI chat message ─────────────────────────────────────────────────────
function ChatMessage({ role, text }: { role: 'user' | 'ai'; text: string }) {
  return (
    <div className={`flex gap-2 ${role === 'user' ? 'flex-row-reverse' : ''}`}>
      <div className={`w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[8px] font-bold ${role === 'user' ? 'bg-violet-600' : 'bg-neutral-700'}`}>
        {role === 'user' ? 'U' : 'AI'}
      </div>
      <div className={`max-w-[80%] px-2.5 py-1.5 rounded-lg text-[10px] leading-relaxed ${role === 'user' ? 'bg-violet-600/20 text-violet-200' : 'bg-neutral-800 text-neutral-300'}`}>
        {text}
      </div>
    </div>
  );
}

// ─── Main Mockup Dashboard ────────────────────────────────────────────────────
export function DashboardMockup() {
  const [typedText, setTypedText] = React.useState('');
  const prompt = 'Write a LinkedIn ad for our Q4 SaaS campaign...';

  React.useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    let i = 0;
    let isDeleting = false;

    const step = () => {
      if (!isDeleting) {
        if (i <= prompt.length) {
          setTypedText(prompt.slice(0, i));
          i++;
          timeoutId = setTimeout(step, 60);
        } else {
          isDeleting = true;
          timeoutId = setTimeout(step, 2500);
        }
      } else {
        setTypedText('');
        i = 0;
        isDeleting = false;
        timeoutId = setTimeout(step, 600);
      }
    };

    timeoutId = setTimeout(step, 400);
    return () => clearTimeout(timeoutId);
  }, []);

  const bars = [28, 42, 36, 56, 48, 62, 52, 72, 60, 80, 68, 76];

  return (
    <div className="relative w-full max-w-[520px] mx-auto lg:mx-0">
      {/* Ambient glow behind */}
      <div className="absolute inset-0 -z-10 bg-violet-600/10 blur-[80px] rounded-full pointer-events-none" />

      {/* Main panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
        className="relative rounded-2xl border border-white/10 bg-neutral-950/80 backdrop-blur-xl overflow-hidden shadow-2xl shadow-black/50"
      >
        {/* Window chrome */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-neutral-900/50">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-500/70" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
          <span className="text-[10px] text-neutral-500 ml-2 font-mono">viptant.ai — AI Workspace</span>
          <div className="ml-auto flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-violet-400 animate-pulse" />
            <span className="text-[9px] text-violet-400 font-medium">AI Active</span>
          </div>
        </div>

        <div className="p-4 space-y-4">
          {/* KPI Row */}
          <div className="grid grid-cols-3 gap-2">
            <KpiCard label="Pipeline Value" value="$2.4M" change="+18% MoM" />
            <KpiCard label="Campaigns Live" value="14" change="+3 this week" />
            <KpiCard label="AI Actions" value="1,284" change="+42% WoW" />
          </div>

          {/* Mini bar chart */}
          <div className="rounded-xl bg-neutral-900/80 border border-white/5 p-3">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] text-neutral-400 font-semibold flex items-center gap-1">
                <BarChart3 className="w-3 h-3" /> Campaign Performance
              </span>
              <span className="text-[9px] text-emerald-400">↑ 34% vs last period</span>
            </div>
            <div className="flex items-end gap-1 h-14">
              {bars.map((h, i) => (
                <MiniBar key={i} height={h * 0.55} active={i >= 8} />
              ))}
            </div>
          </div>

          {/* CRM row */}
          <div className="flex gap-2">
            <div className="flex-1 rounded-xl bg-neutral-900/80 border border-white/5 p-3">
              <div className="flex items-center gap-1 mb-2">
                <Users className="w-3 h-3 text-blue-400" />
                <span className="text-[10px] text-neutral-400 font-semibold">CRM Pipeline</span>
              </div>
              {['Sarah Chen — Enterprise', 'Ama Sarpong — Growth', 'Luis Torres — Startup'].map((name, i) => (
                <div key={i} className="flex items-center justify-between py-1 border-b border-white/5 last:border-0">
                  <span className="text-[9px] text-neutral-300">{name}</span>
                  <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${i === 0 ? 'bg-emerald-500/15 text-emerald-400' : i === 1 ? 'bg-yellow-500/15 text-yellow-400' : 'bg-blue-500/15 text-blue-400'}`}>
                    {i === 0 ? 'HOT' : i === 1 ? 'WARM' : 'NEW'}
                  </span>
                </div>
              ))}
            </div>

            {/* SEO insight widget */}
            <div className="w-28 rounded-xl bg-neutral-900/80 border border-white/5 p-3 flex flex-col gap-2">
              <span className="text-[10px] text-neutral-400 font-semibold flex items-center gap-1">
                <ArrowUpRight className="w-3 h-3 text-violet-400" /> SEO Score
              </span>
              <div className="flex flex-col items-center gap-1 mt-auto">
                <span className="text-2xl font-extrabold text-white">94</span>
                <div className="w-full bg-neutral-800 rounded-full h-1.5">
                  <div className="bg-gradient-to-r from-violet-600 to-indigo-500 h-1.5 rounded-full" style={{ width: '94%' }} />
                </div>
                <span className="text-[8px] text-emerald-400">Top 5%</span>
              </div>
            </div>
          </div>

          {/* AI Chat mini */}
          <div className="rounded-xl bg-neutral-900/80 border border-white/5 p-3 space-y-2">
            <div className="flex items-center gap-1 mb-1">
              <MessageSquare className="w-3 h-3 text-violet-400" />
              <span className="text-[10px] text-neutral-400 font-semibold">AI Agent</span>
            </div>
            <ChatMessage role="ai" text="I analyzed your Q3 performance. Your LinkedIn ads had 3.2× higher CTR than email." />
            <ChatMessage role="user" text={typedText || ' '} />
            <div className="flex gap-2 pt-1">
              <div className="flex-1 px-2.5 py-1.5 rounded-lg bg-neutral-800 border border-white/5 text-[9px] text-neutral-500 flex items-center">
                {typedText}
                <span className="w-0.5 h-3 bg-violet-400 ml-0.5 animate-pulse" />
              </div>
              <button className="p-1.5 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors">
                <Send className="w-3 h-3 text-white" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Floating metric chips using pure CSS float animation without JS transform conflict */}
      <div className="animate-float absolute -top-4 -right-4 bg-neutral-900 border border-emerald-500/20 rounded-xl px-3 py-2 shadow-xl z-10 pointer-events-none">
        <div className="text-[10px] text-emerald-400 font-bold">↑ 127% ROI</div>
        <div className="text-[9px] text-neutral-500">Q4 Campaign</div>
      </div>

      <div className="animate-float-delayed absolute -bottom-3 -left-4 bg-neutral-900 border border-violet-500/20 rounded-xl px-3 py-2 shadow-xl z-10 pointer-events-none">
        <div className="text-[10px] text-violet-400 font-bold flex items-center gap-1">
          <Sparkles className="w-3 h-3" /> AI Generated
        </div>
        <div className="text-[9px] text-neutral-500">48 assets this week</div>
      </div>
    </div>
  );
}
