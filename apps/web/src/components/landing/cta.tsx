'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';

export function CtaSection() {
  return (
    <section className="py-28 relative overflow-hidden">
      {/* Large ambient glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-violet-600/8 blur-[140px] rounded-full" />
      </div>

      <div className="max-w-4xl mx-auto px-6 text-center relative">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col items-center gap-8"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/20 bg-violet-500/8 text-violet-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 animate-pulse" />
            Start your 14-day free trial today
          </div>

          <h2 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.1] bg-clip-text text-transparent bg-gradient-to-br from-white via-white to-neutral-400">
            Ready to Transform
            <br />
            Your Marketing?
          </h2>

          <p className="text-lg text-neutral-500 max-w-xl leading-relaxed">
            Join 2,000+ marketing teams using Viptant to plan smarter, create faster, and grow revenue with AI agents working around the clock.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/auth/register"
              className="group inline-flex items-center gap-2.5 px-8 py-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-base shadow-2xl shadow-violet-500/30 transition-all duration-200 hover:shadow-violet-500/50 hover:scale-[1.02]"
            >
              Start Free — No Credit Card
              <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-xl border border-white/12 bg-white/4 hover:bg-white/8 text-white font-bold text-base backdrop-blur-sm transition-all duration-200"
            >
              Book a Live Demo
            </Link>
          </div>

          <p className="text-sm text-neutral-600">
            No setup fees. Cancel anytime. SOC 2 Type II compliant.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
