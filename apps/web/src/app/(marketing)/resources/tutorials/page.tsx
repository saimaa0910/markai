'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, BookOpen, Key, Clock, ShieldAlert, Sparkles, ChevronRight, HelpCircle 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

interface TextTutorial {
  title: string;
  readTime: string;
  category: string;
  desc: string;
}

interface VideoTutorial {
  title: string;
  duration: string;
  category: string;
  bg: string;
}

const TEXT_TUTORIALS: TextTutorial[] = [
  { title: 'Training Agents on Brand Guidelines PDFs', readTime: '5 min read', category: 'Vault & memory', desc: 'Step-by-step instruction on document preparation, RAG uploading, and parsing parameters sync.' },
  { title: 'Setup Webhook signature verification in Node.js', readTime: '4 min read', category: 'Developers', desc: 'Secure payload checks using SHA-256 HMAC verification code snippets.' },
  { title: 'Configure Auto-Budget campaign throttling', readTime: '8 min read', category: 'Campaigns & ROI', desc: 'Adding budget safety parameters to agents to shut down high CPC triggers autonomously.' },
  { title: 'De-duplicate inbound lead emails semantically', readTime: '6 min read', category: 'CRM database', desc: 'Create AI-driven clean registries based on brand intent logic matches.' },
];

const VIDEO_TUTORIALS: VideoTutorial[] = [
  { title: 'AI Gateway Model Routing Logic', duration: '2:14 mins', category: 'Engineering', bg: 'from-violet-600/30 to-indigo-600/30' },
  { title: 'Authenticating Meta & Google Ads APIs', duration: '3:45 mins', category: 'Channels Integration', bg: 'from-blue-600/30 to-cyan-600/30' },
  { title: 'Orchestrating Outbound Nurture Loops', duration: '4:10 mins', category: 'Agentic Workflows', bg: 'from-emerald-600/30 to-teal-600/30' },
];

export default function TutorialsPage() {
  const [playingVideo, setPlayingVideo] = React.useState<string | null>(null);

  const triggerPlay = (title: string) => {
    setPlayingVideo(title);
    setTimeout(() => setPlayingVideo(null), 3000);
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Learning Center</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Step-by-Step Tutorials
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Master the Viptant system. Watch quick video walk-throughs or read technical integration guides.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Video Tutorials Grid ────────────────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="text-center mb-14">
          <FadeUp>
            <SectionLabel>Video Guides</SectionLabel>
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 text-white">Watch and Learn</h3>
          </FadeUp>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {VIDEO_TUTORIALS.map((vid, idx) => (
            <FadeUp 
              key={vid.title} 
              delay={idx * 0.05}
              className="group rounded-xl border border-white/6 bg-neutral-950/40 overflow-hidden flex flex-col justify-between"
            >
              {/* Graphic play box mockup */}
              <div 
                className={`aspect-video w-full bg-gradient-to-tr ${vid.bg} border-b border-white/5 relative flex items-center justify-center cursor-pointer overflow-hidden`}
                onClick={() => triggerPlay(vid.title)}
              >
                <div className="absolute inset-0 bg-neutral-950/20 group-hover:bg-transparent transition-colors" />
                <div className="w-12 h-12 rounded-full bg-violet-600/80 border border-violet-500/30 flex items-center justify-center text-white shrink-0 group-hover:scale-105 transition-all shadow-xl shadow-black/30">
                  <Play className="w-5 h-5 fill-white text-white ml-0.5" />
                </div>
                <span className="absolute bottom-2 right-3 text-[9px] font-mono text-neutral-400 bg-black/60 px-2 py-0.5 rounded border border-white/5">
                  {vid.duration}
                </span>
              </div>

              <div className="p-6 text-left">
                <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wider block mb-1.5">{vid.category}</span>
                <h4 className="text-sm font-bold text-white mb-2 leading-snug group-hover:text-violet-300 transition-colors">
                  {vid.title}
                </h4>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ─── Text Guides list ───────────────────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30 text-left">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Integration Guides</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Written Walkthroughs
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
            {TEXT_TUTORIALS.map((tut, idx) => (
              <FadeUp 
                key={tut.title} 
                delay={idx * 0.04}
                className="p-6 rounded-xl border border-white/6 bg-black hover:border-violet-500/25 transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <span className="text-[9px] font-bold text-violet-400 uppercase tracking-wider">{tut.category}</span>
                    <span className="flex items-center gap-1 text-[9px] text-neutral-500"><Clock className="w-3 h-3" /> {tut.readTime}</span>
                  </div>
                  <h4 className="text-sm font-bold text-white mb-2 group-hover:text-violet-300 transition-colors">
                    {tut.title}
                  </h4>
                  <p className="text-neutral-400 text-xs leading-relaxed mb-6">{tut.desc}</p>
                </div>
                <a 
                  href="#"
                  className="text-xs font-semibold text-neutral-300 hover:text-white flex items-center gap-1 group/link mt-auto"
                >
                  Read Guide <ChevronRight className="w-3.5 h-3.5 text-violet-400 group-hover/link:translate-x-0.5 transition-all" />
                </a>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* Video Streaming Alert Toast */}
      <AnimatePresence>
        {playingVideo && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 right-6 z-50 p-4 rounded-xl border border-violet-500/30 bg-neutral-950 shadow-2xl max-w-sm flex items-start gap-3"
          >
            <div className="w-8 h-8 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400 shrink-0">
              <Play className="w-4 h-4 fill-violet-400 text-violet-400" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">Streaming Video...</h4>
              <p className="text-[10px] text-neutral-400 mt-0.5 leading-relaxed">
                Now streaming: <strong className="text-violet-300">{playingVideo}</strong> inside sandbox video overlay.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
