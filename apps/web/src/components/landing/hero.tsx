'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, ChevronRight, Play, Sparkles, Star } from 'lucide-react';
import { DashboardMockup } from './dashboard-mockup';
import { FadeUp } from './primitives';

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center pt-24 pb-16 overflow-hidden bg-grid-dots">
      {/* Ambient background glows */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-20%] left-[-10%] w-[700px] h-[700px] rounded-full bg-violet-600/8 blur-[140px]" />
        <div className="absolute top-[30%] right-[-15%] w-[500px] h-[500px] rounded-full bg-indigo-600/8 blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[40%] w-[400px] h-[400px] rounded-full bg-rose-600/5 blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto px-6 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left — Copy & CTAs */}
          <div className="flex flex-col gap-8">
            {/* Pill badge */}
            <FadeUp>
              <div className="flex items-center gap-2">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-violet-500/25 bg-violet-500/8 text-violet-300 text-xs font-semibold">
                  <Sparkles className="w-3 h-3 animate-pulse" />
                  Backed by AI-first enterprise infrastructure
                  <ChevronRight className="w-3 h-3" />
                </div>
              </div>
            </FadeUp>

            {/* Main headline */}
            <FadeUp delay={0.1}>
              <h1 className="text-5xl sm:text-6xl xl:text-7xl font-extrabold tracking-tight leading-[1.05]">
                <span className="bg-clip-text text-transparent bg-gradient-to-br from-white via-white to-neutral-400">
                  The AI-Native
                </span>
                <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-violet-400 via-indigo-300 to-violet-400 animate-gradient-x">
                  Marketing OS
                </span>
              </h1>
            </FadeUp>

            {/* Subheadline */}
            <FadeUp delay={0.2}>
              <p className="text-lg sm:text-xl text-neutral-400 leading-relaxed max-w-lg">
                One intelligent platform to{' '}
                <span className="text-neutral-200">create content</span>,{' '}
                <span className="text-neutral-200">manage CRM</span>,{' '}
                <span className="text-neutral-200">automate campaigns</span>,{' '}
                analyze performance and collaborate with{' '}
                <span className="text-violet-400">AI Agents</span>.
              </p>
            </FadeUp>

            {/* CTA row */}
            <FadeUp delay={0.3}>
              <div className="flex flex-wrap items-center gap-4">
                <Link
                  href="/auth/register"
                  className="group inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-violet-500/25 transition-all duration-200 hover:shadow-violet-500/40 hover:scale-[1.02]"
                >
                  Start Free
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </Link>
                <Link
                  href="/auth/login"
                  className="group inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl border border-white/12 bg-white/4 hover:bg-white/8 text-white font-semibold text-sm backdrop-blur-sm transition-all duration-200"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Book Demo
                </Link>
              </div>
            </FadeUp>

            {/* Social proof */}
            <FadeUp delay={0.4}>
              <div className="flex items-center gap-4 pt-2">
                <div className="flex -space-x-2">
                  {['🧑🏽‍💼', '👩🏻‍💼', '🧑🏾‍💼', '👩🏼‍💼', '👨🏿‍💼'].map((emoji, i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full bg-neutral-800 border-2 border-black flex items-center justify-center text-sm"
                    >
                      {emoji}
                    </div>
                  ))}
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    Trusted by{' '}
                    <span className="text-neutral-300 font-semibold">2,000+</span> marketing teams
                  </p>
                </div>
              </div>
            </FadeUp>
          </div>

          {/* Right — Animated dashboard mockup */}
          <div className="flex justify-center lg:justify-end">
            <DashboardMockup />
          </div>
        </div>
      </div>
    </section>
  );
}
