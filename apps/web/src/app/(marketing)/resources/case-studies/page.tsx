'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Building, TrendingUp, Clock, Target, ArrowRight, Sparkles, ChevronRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

interface CaseStudy {
  slug: string;
  company: string;
  industry: string;
  tagline: string;
  challenge: string;
  roi: string;
  roiLabel: string;
  logoColor: string;
}

const CASES: CaseStudy[] = [
  {
    slug: 'retool-crm-enrichment',
    company: 'Retool',
    industry: 'Developer Tools',
    tagline: 'Automating sales lead enrichment using CRM agents scraping context.',
    challenge: 'Manual sales profiling was delaying email outreach by up to 24 hours. CRM agents solved enrichment in <4 minutes.',
    roi: '+140%',
    roiLabel: 'Outbound pipeline growth',
    logoColor: 'from-orange-600/30 to-amber-600/30',
  },
  {
    slug: 'lattice-newsletter-scale',
    company: 'Lattice',
    industry: 'HR Tech',
    tagline: 'Scaling custom outbox newsletter copywriting across 12 segment cohorts.',
    challenge: 'Writers spent days drafting personalized variations. Content Studio generated on-brand cohorts copies in seconds.',
    roi: '30 hrs',
    roiLabel: 'Saved weekly per writer',
    logoColor: 'from-blue-600/30 to-indigo-600/30',
  },
  {
    slug: 'vercel-gateway-routing',
    company: 'Vercel',
    industry: 'Cloud Infrastructure',
    tagline: 'Optimizing high-throughput token costs using AI Gateway models routing.',
    challenge: 'Using GPT-4o for simple schema checks was generating high bills. Routing dynamically saved budget.',
    roi: '-38%',
    roiLabel: 'Token cost reductions',
    logoColor: 'from-neutral-800 to-neutral-900',
  },
];

const INDUSTRIES = ['All', 'Developer Tools', 'HR Tech', 'Cloud Infrastructure'];

export default function CaseStudiesPage() {
  const router = useRouter();
  const [selectedInd, setSelectedInd] = React.useState('All');

  const filteredCases = CASES.filter(
    (c) => selectedInd === 'All' || c.industry === selectedInd
  );

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Customer Stories</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Real Teams. Real Marketing ROI.
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Explore how high-performing B2B and SaaS software companies leverage Viptant AI Agents to automate operations and scaling pipelines.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Featured Customer Case Banner ────────────────────────────────── */}
      <section className="py-12 max-w-7xl mx-auto px-6">
        <FadeUp>
          <div className="group relative rounded-2xl border border-white/10 bg-neutral-950/40 overflow-hidden flex flex-col lg:flex-row gap-8 hover:border-violet-500/30 hover:bg-neutral-900/10 transition-all duration-300 p-8 sm:p-10">
            <div className="absolute inset-0 bg-gradient-to-tr from-violet-600/5 via-indigo-600/5 to-transparent pointer-events-none" />
            
            {/* Visual Cover logo box */}
            <div className="w-full lg:w-1/2 aspect-video rounded-xl bg-gradient-to-tr from-violet-600/30 to-fuchsia-600/30 flex items-center justify-center shrink-0 border border-white/5 overflow-hidden relative">
              <span className="text-4xl font-extrabold text-white tracking-widest opacity-40">LINEAR</span>
            </div>

            {/* Details */}
            <div className="flex flex-col justify-between py-2 text-left">
              <div>
                <span className="px-2.5 py-0.5 rounded-full border border-violet-500/20 bg-violet-500/5 text-xs font-semibold text-violet-400 uppercase tracking-wider block mb-4 w-max">
                  Featured Case Study
                </span>
                
                <h3 className="text-xl sm:text-2xl font-bold text-white mb-4 group-hover:text-violet-300 transition-colors leading-snug">
                  How Linear Scales Ad Copy Syndication Autonomously by 8×
                </h3>
                
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-6">
                  Linear integrated Viptant Content Studio and Campaign scheduling with their developer release pipelines to write and syndicate feature announcements across channels.
                </p>
              </div>

              {/* Stat row */}
              <div className="grid grid-cols-3 gap-4 border-t border-white/5 pt-6 mt-6">
                <div>
                  <span className="text-2xl sm:text-3xl font-extrabold text-white">8×</span>
                  <span className="text-[9px] text-neutral-500 uppercase block">Ad Volume Scaled</span>
                </div>
                <div>
                  <span className="text-2xl sm:text-3xl font-extrabold text-white">3.4%</span>
                  <span className="text-[9px] text-neutral-500 uppercase block">Click CTR Gains</span>
                </div>
                <div>
                  <span className="text-2xl sm:text-3xl font-extrabold text-white">-45%</span>
                  <span className="text-[9px] text-neutral-500 uppercase block">Marketer Hours Spent</span>
                </div>
              </div>
            </div>
          </div>
        </FadeUp>
      </section>

      {/* ─── Filter Section & Stories Grid ───────────────────────────────── */}
      <section className="py-12 max-w-7xl mx-auto px-6 text-left">
        {/* Industry tab selector */}
        <div className="flex items-center gap-1.5 overflow-x-auto justify-start py-2 mb-10 border-b border-white/5 scrollbar-none">
          {INDUSTRIES.map((ind) => (
            <button
              key={ind}
              onClick={() => setSelectedInd(ind)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                selectedInd === ind
                  ? 'bg-violet-600 text-white'
                  : 'bg-neutral-900 border border-white/5 text-neutral-400 hover:text-white'
              }`}
            >
              {ind}
            </button>
          ))}
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <AnimatePresence mode="wait">
            {filteredCases.map((cs, idx) => (
              <motion.div
                key={cs.slug}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.25, delay: idx * 0.04 }}
                className="group p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/25 hover:bg-neutral-900/10 transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Mock logo wrapper */}
                  <div className={`w-full aspect-video rounded-lg bg-gradient-to-tr ${cs.logoColor} border border-white/5 flex items-center justify-center mb-5`}>
                    <span className="text-xl font-bold text-white tracking-wider opacity-30">{cs.company}</span>
                  </div>

                  <span className="text-[9px] font-bold text-violet-400 uppercase tracking-wider block mb-1">{cs.industry}</span>
                  <h4 className="text-base font-bold text-white mb-2 leading-snug group-hover:text-violet-300 transition-colors">
                    {cs.tagline}
                  </h4>
                  <p className="text-neutral-400 text-xs leading-relaxed mb-6">{cs.challenge}</p>
                </div>

                <div className="flex items-center justify-between border-t border-white/5 pt-4 mt-auto">
                  <div>
                    <span className="text-lg font-extrabold text-white block">{cs.roi}</span>
                    <span className="text-[8px] text-neutral-500 uppercase tracking-wider font-semibold block">{cs.roiLabel}</span>
                  </div>

                  <a 
                    href="#" 
                    className="text-xs font-semibold text-neutral-300 hover:text-white flex items-center gap-1 group/link"
                  >
                    Read Story <ChevronRight className="w-3.5 h-3.5 text-violet-400 group-hover/link:translate-x-0.5 transition-all" />
                  </a>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </section>

      {/* ─── Bottom testimonial quotes banner ───────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50 text-center relative overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-violet-600/5 blur-[120px] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <FadeUp>
            <p className="text-xl sm:text-2xl text-neutral-300 italic max-w-2xl mx-auto leading-relaxed mb-6 font-serif">
              "Viptant completely solved our outbound data profiling. Our sales reps save hours every week, and lead pipeline enrichment accuracy has reached 99%."
            </p>
            <span className="text-xs font-bold text-white block mb-0.5">Head of Revenue Operations</span>
            <span className="text-[10px] text-neutral-500 uppercase tracking-widest font-semibold block">Developer Platform Startup</span>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}
