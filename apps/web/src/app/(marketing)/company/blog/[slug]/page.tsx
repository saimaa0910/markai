'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Calendar, Clock, ArrowLeft, Share2, Sparkles, Send, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading } from '@/components/landing/primitives';
import { MOCK_POSTS, BlogPost } from '../page';

export default function BlogDetailsPage({ 
  params 
}: { 
  params: Promise<{ slug: string }> 
}) {
  const router = useRouter();
  const { slug } = React.use(params);
  const [copied, setCopied] = React.useState(false);

  const post = MOCK_POSTS.find((p) => p.slug === slug);

  if (!post) {
    return (
      <div className="bg-black text-white font-sans min-h-screen flex flex-col items-center justify-center p-6 text-center">
        <h2 className="text-2xl font-bold mb-3">Article Not Found</h2>
        <p className="text-neutral-500 mb-8 text-sm">The article you are looking for does not exist or has been relocated.</p>
        <Button variant="violet" onClick={() => router.push('/company/blog')}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Blog
        </Button>
      </div>
    );
  }

  // Get related posts (exclude current, take up to 3)
  const relatedPosts = MOCK_POSTS.filter((p) => p.slug !== post.slug).slice(0, 3);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen pb-20">
      {/* ─── Breadcrumb Back Navigation ──────────────────────────────────── */}
      <div className="max-w-4xl mx-auto px-6 pt-12">
        <FadeUp>
          <button
            onClick={() => router.push('/company/blog')}
            className="inline-flex items-center gap-2 text-xs font-semibold text-neutral-400 hover:text-white transition-colors cursor-pointer group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Back to Journal
          </button>
        </FadeUp>
      </div>

      {/* ─── Article Header ─────────────────────────────────────────────── */}
      <header className="max-w-4xl mx-auto px-6 pt-8 pb-10 border-b border-white/5">
        <FadeUp delay={0.05}>
          <div className="flex items-center gap-3.5 text-xs text-violet-400 mb-5">
            <span className="px-2.5 py-0.5 rounded-full border border-violet-500/20 bg-violet-500/5 font-semibold uppercase tracking-wider">
              {post.category}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-neutral-500" /> {post.date}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-neutral-500" /> {post.readTime}
            </span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-6 leading-tight">
            {post.title}
          </h1>

          <p className="text-neutral-400 text-sm sm:text-base leading-relaxed max-w-3xl mb-8">
            {post.summary}
          </p>

          <div className="flex items-center justify-between pt-4">
            {/* Author */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-sm text-violet-300">
                {post.authorInitials}
              </div>
              <div>
                <p className="text-sm font-bold text-white">{post.author}</p>
                <p className="text-xs text-neutral-500">{post.authorTitle}</p>
              </div>
            </div>

            {/* Share / Action Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleShare}
              className="h-9 gap-1.5 text-xs text-neutral-400 hover:text-white"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied Link
                </>
              ) : (
                <>
                  <Share2 className="w-3.5 h-3.5" /> Share Article
                </>
              )}
            </Button>
          </div>
        </FadeUp>
      </header>

      {/* ─── Article Body ───────────────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <FadeUp delay={0.1}>
          {/* Cover Graphic Visual */}
          <div className={`w-full aspect-video rounded-2xl bg-gradient-to-tr ${post.bg} flex items-center justify-center border border-white/8 mb-12`}>
            <Sparkles className="w-16 h-16 text-violet-400/25" />
          </div>

          <article className="prose prose-invert prose-violet max-w-none space-y-6 text-neutral-300 leading-relaxed text-sm sm:text-base">
            <h2 className="text-xl sm:text-2xl font-bold text-white pt-4">The Shift to Agentic Autonomy</h2>
            <p>
              Historically, automation in marketing has meant setting up rigid, rule-based workflows: "If a user registers, wait 2 hours, then send email X." While this functions for simple triggers, it breaks down immediately when faced with real-world complexity, customer nuances, or multivariate testing strategies.
            </p>
            <p>
              An **agentic workflow**, by contrast, leverages LLMs as decision-making hubs. Rather than following a locked step, the agent is given a goal: "Optimize email engagement for new sign-ups." The agent is equipped with tools—email composers, AB test runners, cohort query tables, and performance analytics—and autonomously decides which actions to take, monitors the output, and self-corrects based on immediate conversions.
            </p>

            <blockquote className="border-l-2 border-violet-500 pl-4 py-2 my-6 bg-neutral-900/30 rounded-r-lg text-neutral-400 italic text-sm">
              "We are moving from a world where humans tell systems precisely how to click buttons, to a world where we provide systems with goals, boundaries, and contextual data, and trust them to discover the optimal path."
            </blockquote>

            <h2 className="text-xl sm:text-2xl font-bold text-white pt-4">Key Foundations of the Architecture</h2>
            <p>
              Building a system capable of this scale requires solving three foundational engineering bottlenecks:
            </p>
            <ul className="list-disc pl-6 space-y-2.5">
              <li>
                <strong className="text-white">Dynamic Context Injection:</strong> Agents must access updated brand profiles, customer segments, and style guides. We solve this using isolated vector indexing per tenant.
              </li>
              <li>
                <strong className="text-white">Smart Routing Control:</strong> Running expensive LLMs for simple tasks is inefficient. The system must evaluate prompts and route them dynamically to models optimized for accuracy or speed.
              </li>
              <li>
                <strong className="text-white">Structured Guardrails:</strong> Campaigns must comply with legal standards (GDPR, TCPA) and brand safety limits. The Viptant engine intercepts all agent calls to validate structured output schemas.
              </li>
            </ul>

            <h2 className="text-xl sm:text-2xl font-bold text-white pt-4">Looking Forward</h2>
            <p>
              As we scale Viptant towards support for hundreds of custom fine-tuned models, we are focused on latency reduction and deterministic safety validation. We believe agentic marketing will not just increase volume; it will fundamentally elevate the quality of user experiences by tailoring content semantically to individual needs.
            </p>
          </article>
        </FadeUp>
      </section>

      {/* ─── Author Biography Card ───────────────────────────────────────── */}
      <section className="max-w-3xl mx-auto px-6 py-8 border-y border-white/5 bg-neutral-950/20 rounded-2xl my-16">
        <FadeUp>
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className="w-16 h-16 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-xl text-violet-300 shrink-0">
              {post.authorInitials}
            </div>
            <div className="text-center sm:text-left flex-1">
              <h4 className="text-base font-bold text-white mb-0.5">{post.author}</h4>
              <p className="text-xs font-semibold text-violet-400 mb-3">{post.authorTitle} at Viptant</p>
              <p className="text-xs text-neutral-400 leading-relaxed">
                {post.author} is a lead contributor at Viptant, specializing in building high-fidelity agent systems and AI architectures. Prior to joining Viptant, {post.author.split(' ')[1]} worked at leading tech research institutes.
              </p>
            </div>
          </div>
        </FadeUp>
      </section>

      {/* ─── Related Articles Grid ──────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 border-t border-white/5 pt-16">
        <FadeUp>
          <h3 className="text-xl sm:text-2xl font-bold text-white mb-10 text-center sm:text-left">
            Related Articles
          </h3>
        </FadeUp>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {relatedPosts.map((r, i) => (
            <FadeUp
              key={r.slug}
              delay={i * 0.05}
            >
              <div
                onClick={() => router.push(`/company/blog/${r.slug}`)}
                className="group relative rounded-xl border border-white/6 bg-neutral-950/40 overflow-hidden flex flex-col hover:border-violet-500/20 hover:bg-neutral-900/10 transition-all duration-300 cursor-pointer h-full text-left"
              >
                <div className={`w-full aspect-video bg-gradient-to-tr ${r.bg} flex items-center justify-center shrink-0`}>
                  <Sparkles className="w-6 h-6 text-violet-400/20 group-hover:scale-110 transition-transform duration-300" />
                </div>
                <div className="p-5 flex-1 flex flex-col justify-between">
                  <div>
                    <span className="text-[9px] font-bold text-violet-400 uppercase tracking-wider mb-2 block">{r.category}</span>
                    <h4 className="text-sm font-bold text-white mb-2 group-hover:text-violet-300 transition-colors leading-snug line-clamp-2">
                      {r.title}
                    </h4>
                  </div>
                  <div className="flex items-center justify-between border-t border-white/5 pt-3 mt-4 text-[10px] text-neutral-500">
                    <span>{r.date}</span>
                    <span className="text-neutral-400 font-medium">Read Post →</span>
                  </div>
                </div>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>
    </div>
  );
}
