'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Calendar, Clock, ArrowRight, Sparkles, Mail, Rss, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

export interface BlogPost {
  slug: string;
  title: string;
  category: string;
  summary: string;
  date: string;
  readTime: string;
  author: string;
  authorTitle: string;
  authorInitials: string;
  tags: string[];
  bg: string;
}

export const MOCK_POSTS: BlogPost[] = [
  {
    slug: 'unlocking-agentic-workflows',
    title: 'Unlocking Agentic Workflows: The Future of Campaign Automation',
    category: 'Engineering',
    summary: 'How multi-agent architectures are replacing linear, logic-locked integrations (like Zapier) to build self-correcting marketing pipelines that adapt to conversion data.',
    date: 'July 12, 2026',
    readTime: '8 min read',
    author: 'Dr. Sarah Chen',
    authorTitle: 'Chief Scientist',
    authorInitials: 'SC',
    tags: ['AI Agents', 'Orchestration', 'LLMs'],
    bg: 'from-violet-600/20 to-indigo-600/20',
  },
  {
    slug: 'mastering-crm-data-pipelines',
    title: 'Mastering CRM Data Pipelines: Cleaning Lead Sourcing with AI',
    category: 'Data & CRM',
    summary: 'Learn how automated agents sanitize and enrich inbound sales leads using real-time semantic scraping and corporate registry matching to keep databases 100% clean.',
    date: 'July 8, 2026',
    readTime: '5 min read',
    author: 'Marcus Vance',
    authorTitle: 'VP of Engineering',
    authorInitials: 'MV',
    tags: ['CRM', 'Automation', 'Data Science'],
    bg: 'from-blue-600/20 to-cyan-600/20',
  },
  {
    slug: 'ten-ways-to-write-better-ad-prompts',
    title: '10 Ways to Write Better Ad Prompts for Generative Writers',
    category: 'Content Strategy',
    summary: 'A deep dive into system prompts, template injections, and few-shot examples that align AI outputs with your brand guidelines and improve click-through rates by 40%.',
    date: 'July 3, 2026',
    readTime: '6 min read',
    author: 'Elena Rostova',
    authorTitle: 'Head of Design',
    authorInitials: 'ER',
    tags: ['Generative Copy', 'Prompts', 'ROI'],
    bg: 'from-amber-600/20 to-rose-600/20',
  },
  {
    slug: 'scaling-to-series-b',
    title: 'Scaling Viptant to 2,000+ Enterprise Marketing Teams',
    category: 'Company',
    summary: 'An inside look at our engineering milestones, vector database replication configurations, and our recent successful SOC 2 Type II audit to guarantee customer safety.',
    date: 'June 25, 2026',
    readTime: '12 min read',
    author: 'Alex Rivera',
    authorTitle: 'Co-Founder & CEO',
    authorInitials: 'AR',
    tags: ['Scaling', 'Security', 'Infrastructure'],
    bg: 'from-violet-600/20 to-pink-600/20',
  },
  {
    slug: 'evaluating-reasoning-models',
    title: 'Evaluating Reasoning Models in Marketing Contexts',
    category: 'Research',
    summary: 'How Claude 3.5 Sonnet, GPT-4o, and Gemini 1.5 Pro compare in planning budgets, scheduling multi-channel posts, and executing complex brand-alignment directives.',
    date: 'June 18, 2026',
    readTime: '9 min read',
    author: 'Dr. Sarah Chen',
    authorTitle: 'Chief Scientist',
    authorInitials: 'SC',
    tags: ['LLM Benchmarks', 'Gemini', 'Claude'],
    bg: 'from-emerald-600/20 to-teal-600/20',
  },
  {
    slug: 'designing-for-low-latency-ai',
    title: 'Designing User Interfaces for Low-Latency AI Feedbacks',
    category: 'Design',
    summary: 'How micro-interactions, optimistic updates, and partial stream displays make slower LLM completion times feel instantaneous, increasing user retention.',
    date: 'June 10, 2026',
    readTime: '4 min read',
    author: 'Elena Rostova',
    authorTitle: 'Head of Design',
    authorInitials: 'ER',
    tags: ['UX Design', 'Streaming UI', 'Next.js'],
    bg: 'from-rose-600/20 to-purple-600/20',
  },
];

const CATEGORIES = ['All', 'Engineering', 'Data & CRM', 'Content Strategy', 'Company', 'Research', 'Design'];

export default function BlogListingPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState('All');
  const [emailSubscribed, setEmailSubscribed] = React.useState(false);
  const [email, setEmail] = React.useState('');

  const featured = MOCK_POSTS[0];
  const remaining = MOCK_POSTS.slice(1);

  const filteredPosts = remaining.filter((post) => {
    const matchesCategory = selectedCategory === 'All' || post.category === selectedCategory;
    const matchesSearch = 
      post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setEmailSubscribed(true);
      setEmail('');
    }
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Header Hero ─────────────────────────────────────────────────── */}
      <section className="relative pt-20 pb-12 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Viptant Journal</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Insights on AI, Design, and Marketing Engineering
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Discover engineering breakdowns, UX blueprints, and operational updates from the team building Viptant.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Featured Article Hero ────────────────────────────────────────── */}
      <section className="py-12 max-w-7xl mx-auto px-6">
        <FadeUp>
          <div 
            onClick={() => router.push(`/company/blog/${featured.slug}`)}
            className="group relative rounded-2xl border border-white/10 bg-neutral-950/40 overflow-hidden flex flex-col lg:flex-row gap-8 hover:border-violet-500/30 hover:bg-neutral-900/10 transition-all duration-300 cursor-pointer p-6 sm:p-8"
          >
            {/* Ambient background glow */}
            <div className="absolute inset-0 bg-gradient-to-tr from-violet-600/5 via-indigo-600/5 to-transparent pointer-events-none" />
            
            {/* Visual Cover Graphic */}
            <div className={`w-full lg:w-1/2 aspect-video rounded-xl bg-gradient-to-tr ${featured.bg} flex items-center justify-center shrink-0 border border-white/5 overflow-hidden`}>
              <Sparkles className="w-12 h-12 text-violet-400/40 group-hover:scale-110 transition-transform duration-300" />
            </div>

            {/* Details */}
            <div className="flex flex-col justify-between py-2">
              <div>
                <div className="flex items-center gap-3.5 text-xs text-violet-400 mb-4">
                  <span className="px-2.5 py-0.5 rounded-full border border-violet-500/20 bg-violet-500/5 font-semibold uppercase tracking-wider">{featured.category}</span>
                  <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {featured.date}</span>
                  <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {featured.readTime}</span>
                </div>
                
                <h3 className="text-xl sm:text-2xl font-bold text-white mb-4 group-hover:text-violet-300 transition-colors leading-snug">
                  {featured.title}
                </h3>
                
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-6">
                  {featured.summary}
                </p>
              </div>

              <div className="flex items-center justify-between mt-auto border-t border-white/5 pt-4">
                {/* Author Info */}
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-xs text-violet-300">
                    {featured.authorInitials}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-white">{featured.author}</p>
                    <p className="text-[10px] text-neutral-500">{featured.authorTitle}</p>
                  </div>
                </div>

                <span className="text-xs font-semibold text-neutral-300 flex items-center gap-1 group-hover:text-white group-hover:translate-x-1 transition-all">
                  Read Article <ArrowRight className="w-3.5 h-3.5 text-violet-400" />
                </span>
              </div>
            </div>
          </div>
        </FadeUp>
      </section>

      {/* ─── Search & Category Filtering ──────────────────────────────────── */}
      <section className="py-6 border-y border-white/5 bg-neutral-950/40 relative z-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row gap-6 justify-between items-center">
          {/* Categories Tab Bar */}
          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto py-1 scrollbar-none">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                  selectedCategory === cat
                    ? 'bg-violet-600 text-white'
                    : 'bg-neutral-900 border border-white/5 text-neutral-400 hover:text-white hover:border-white/10'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-neutral-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search articles, tags..."
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </div>
        </div>
      </section>

      {/* ─── Blog Articles Grid ─────────────────────────────────────────── */}
      <section className="py-16 max-w-7xl mx-auto px-6 relative">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredPosts.length > 0 ? (
            filteredPosts.map((post, i) => (
              <FadeUp 
                key={post.slug} 
                delay={i * 0.05}
              >
                <div
                  onClick={() => router.push(`/company/blog/${post.slug}`)}
                  className="group relative rounded-xl border border-white/6 bg-neutral-950/40 overflow-hidden flex flex-col hover:border-violet-500/20 hover:bg-neutral-900/10 transition-all duration-300 cursor-pointer text-left h-full"
                >
                  {/* Image / Gradient Header */}
                  <div className={`w-full aspect-video bg-gradient-to-tr ${post.bg} flex items-center justify-center shrink-0 border-b border-white/5`}>
                    <Sparkles className="w-8 h-8 text-violet-400/20 group-hover:scale-110 transition-transform duration-300" />
                  </div>

                  {/* Content */}
                  <div className="p-6 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-3.5 text-[10px] text-neutral-400 mb-3">
                        <span className="text-violet-400 font-bold uppercase tracking-wider">{post.category}</span>
                        <span>·</span>
                        <span>{post.date}</span>
                      </div>

                      <h4 className="text-base font-bold text-white mb-2.5 group-hover:text-violet-300 transition-colors leading-snug">
                        {post.title}
                      </h4>

                      <p className="text-neutral-400 text-xs leading-relaxed line-clamp-3 mb-6">
                        {post.summary}
                      </p>
                    </div>

                    <div className="flex items-center justify-between border-t border-white/5 pt-4 mt-auto">
                      {/* Author mini profile */}
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-[10px] text-violet-300">
                          {post.authorInitials}
                        </div>
                        <div>
                          <p className="text-[10px] font-semibold text-white">{post.author}</p>
                        </div>
                      </div>

                      <span className="text-[10px] font-semibold text-neutral-400 flex items-center gap-1 group-hover:text-white transition-colors">
                        Read <ArrowRight className="w-3 h-3 text-violet-400" />
                      </span>
                    </div>
                  </div>
                </div>
              </FadeUp>
            ))
          ) : (
            <div className="col-span-full py-16 text-center text-neutral-500 flex flex-col items-center justify-center gap-3">
              <Rss className="w-8 h-8 opacity-25" />
              <p className="text-sm">No articles match your search criteria.</p>
            </div>
          )}
        </div>

        {/* Minimalist Pagination controls */}
        <div className="flex items-center justify-center gap-6 mt-16 pt-8 border-t border-white/5">
          <Button variant="outline" size="sm" className="h-9 px-4 text-xs text-neutral-400 disabled:opacity-40" disabled>
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Previous
          </Button>
          <span className="text-xs text-neutral-500 font-mono">Page 1 of 1</span>
          <Button variant="outline" size="sm" className="h-9 px-4 text-xs text-neutral-400 disabled:opacity-40" disabled>
            Next <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </div>
      </section>

      {/* ─── Newsletter Banner Section ─────────────────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <FadeUp>
            <div className="w-12 h-12 rounded-full bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400 mx-auto mb-6">
              <Mail className="w-5 h-5" />
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-2.5">
              Subscribe to Viptant Operations
            </h3>
            <p className="text-neutral-400 text-xs sm:text-sm max-w-md mx-auto leading-relaxed mb-8">
              Stay ahead on AI system design, marketing workflow orchestration, and SaaS scaling. Delivered weekly.
            </p>

            <AnimatePresence mode="wait">
              {!emailSubscribed ? (
                <motion.form 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  onSubmit={handleSubscribe} 
                  className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
                >
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="flex-1 px-4 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                  />
                  <Button type="submit" variant="violet" className="h-10 px-5 font-semibold text-xs shrink-0">
                    Subscribe Newsletter
                  </Button>
                </motion.form>
              ) : (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-xs font-semibold max-w-sm mx-auto"
                >
                  ✓ Thank you! You have successfully subscribed to Viptant Journal.
                </motion.div>
              )}
            </AnimatePresence>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}
