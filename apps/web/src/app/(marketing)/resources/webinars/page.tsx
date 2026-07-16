'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, Calendar, Clock, Video, Sparkles, 
  ArrowRight, CheckCircle2, ChevronRight, User 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

interface PastWebinar {
  title: string;
  speaker: string;
  speakerTitle: string;
  duration: string;
  bg: string;
}

const PAST_WEBINARS: PastWebinar[] = [
  {
    title: 'Model Cost Diagnostics and AI Gateway Optimization',
    speaker: 'Dr. Sarah Chen',
    speakerTitle: 'Chief Scientist',
    duration: '28 mins',
    bg: 'from-violet-600/30 to-indigo-600/30',
  },
  {
    title: 'Orchestrating Outbox Personalization Cohorts',
    speaker: 'Alex Rivera',
    speakerTitle: 'CEO',
    duration: '42 mins',
    bg: 'from-blue-600/30 to-cyan-600/30',
  },
  {
    title: 'Integrating Vector Vaults Contexts with Salesforce CRM',
    speaker: 'Marcus Vance',
    speakerTitle: 'VP of Engineering',
    duration: '35 mins',
    bg: 'from-emerald-600/30 to-teal-600/30',
  },
];

export default function WebinarsPage() {
  const [registered, setRegistered] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [playingVideo, setPlayingVideo] = React.useState<string | null>(null);

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setRegistered(true);
    }, 1000);
  };

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
            <SectionLabel>Viptant Live</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Webinars and Masterclasses
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Join live technical demonstrations led by our engineering founders, or explore archived recordings covering agent design.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Upcoming Live Webinar Box ──────────────────────────────────── */}
      <section className="py-12 max-w-5xl mx-auto px-6">
        <FadeUp>
          <div className="group relative rounded-2xl border border-white/10 bg-neutral-950/40 overflow-hidden flex flex-col lg:flex-row gap-8 hover:border-violet-500/30 hover:bg-neutral-900/10 transition-all duration-300 p-8 text-left">
            <div className="absolute inset-0 bg-gradient-to-tr from-violet-600/5 via-indigo-600/5 to-transparent pointer-events-none" />
            
            {/* Countdown info column (col-span-1) */}
            <div className="w-full lg:w-1/2 flex flex-col justify-between space-y-6">
              <div>
                <span className="px-2.5 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-xs font-semibold text-emerald-400 uppercase tracking-wider block mb-4 w-max">
                  Upcoming Broadcast
                </span>
                
                <h3 className="text-xl sm:text-2xl font-bold text-white mb-4 leading-snug">
                  Orchestrating AI Agents for Q4 Campaign Deliveries
                </h3>
                
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-6">
                  Learn how to configure multi-agent workflow branches, map custom variables contexts, and set cost thresholds budget caps before holiday ads deploy.
                </p>
              </div>

              {/* Time slot details */}
              <div className="flex items-center gap-6 text-xs text-neutral-300">
                <span className="flex items-center gap-1.5"><Calendar className="w-4 h-4 text-violet-400" /> July 28, 2026</span>
                <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-violet-400" /> 11:00 AM EST</span>
                <span className="flex items-center gap-1.5"><Video className="w-4 h-4 text-violet-400" /> Live Stream</span>
              </div>
            </div>

            {/* Registration Form column (col-span-1) */}
            <div className="w-full lg:w-1/2 p-6 rounded-xl border border-white/5 bg-black flex flex-col justify-center relative">
              <AnimatePresence mode="wait">
                {!registered ? (
                  <motion.form 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onSubmit={handleRegister} 
                    className="space-y-4"
                  >
                    <h4 className="text-sm font-bold text-white mb-2">Reserve Your Stream Seat</h4>
                    <input
                      type="email"
                      required
                      placeholder="name@company.com"
                      className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                    />
                    <Button
                      type="submit"
                      variant="violet"
                      className="w-full h-10 text-xs font-semibold"
                      isLoading={loading}
                    >
                      Register Live Webinar
                    </Button>
                    <span className="text-[10px] text-neutral-500 block text-center mt-2">Starts in 14 days. Calendar invite sent upon signup.</span>
                  </motion.form>
                ) : (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="py-6 text-center space-y-4"
                  >
                    <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white">Seat Reserved!</h4>
                      <p className="text-[10px] text-neutral-400 mt-1 leading-relaxed max-w-xs mx-auto">
                        Your calendar invitation has been sent to your email. We look forward to seeing you live on July 28.
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </FadeUp>
      </section>

      {/* ─── Past Webinars Grid Section ─────────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30 text-left">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Archive</SectionLabel>
              <GradientHeading className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2">
                Past Recordings
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {PAST_WEBINARS.map((vid, idx) => (
              <FadeUp 
                key={vid.title} 
                delay={idx * 0.05}
                className="group rounded-xl border border-white/6 bg-black overflow-hidden flex flex-col justify-between"
              >
                {/* Visual playback mockup box */}
                <div 
                  className={`aspect-video w-full bg-gradient-to-tr ${vid.bg} border-b border-white/5 relative flex items-center justify-center cursor-pointer overflow-hidden`}
                  onClick={() => triggerPlay(vid.title)}
                >
                  <div className="absolute inset-0 bg-neutral-950/20 group-hover:bg-transparent transition-colors" />
                  <div className="w-10 h-10 rounded-full bg-violet-600/80 border border-violet-500/30 flex items-center justify-center text-white shrink-0 group-hover:scale-105 transition-all shadow-xl shadow-black/30">
                    <Play className="w-4 h-4 fill-white text-white ml-0.5" />
                  </div>
                  <span className="absolute bottom-2 right-3 text-[8px] font-mono text-neutral-400 bg-black/60 px-2 py-0.5 rounded border border-white/5">
                    {vid.duration}
                  </span>
                </div>

                <div className="p-6">
                  <h4 className="text-sm font-bold text-white mb-4 leading-snug group-hover:text-violet-300 transition-colors">
                    {vid.title}
                  </h4>
                  
                  {/* Speaker Details */}
                  <div className="flex items-center justify-between border-t border-white/5 pt-4 text-[10px] text-neutral-500">
                    <div className="flex items-center gap-1.5"><User className="w-3.5 h-3.5 text-neutral-600" /> {vid.speaker}</div>
                    <span>{vid.speakerTitle}</span>
                  </div>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* Video Streaming Notification Toast */}
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
              <h4 className="text-xs font-bold text-white">Streaming Webinar...</h4>
              <p className="text-[10px] text-neutral-400 mt-0.5 leading-relaxed">
                Loading recording: <strong className="text-violet-300">{playingVideo}</strong> inside sandbox interface.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
