'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, BookOpen, Key, Database, Megaphone, GitBranch, 
  HelpCircle, ChevronRight, Sparkles, ArrowRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

interface DocCategory {
  title: string;
  desc: string;
  icon: any;
  articles: { title: string; href: string; excerpt: string }[];
}

const CATEGORIES: DocCategory[] = [
  {
    title: 'Core Concepts',
    desc: 'Understand the foundations of the Viptant agentic marketing operating system.',
    icon: BookOpen,
    articles: [
      { title: 'What is Viptant?', href: '/company/about', excerpt: 'An overview of our agentic workflow orchestration model.' },
      { title: 'Platform Quickstart Guide', href: '/auth/register', excerpt: 'Create an account and launch your first AI agent in 5 minutes.' },
      { title: 'Glossary & Taxonomy', href: '#', excerpt: 'Key definitions: Agents, Gateway, Vault, Prompt Variables.' },
    ],
  },
  {
    title: 'SDK & Client Setup',
    desc: 'Install dependencies and initialize client connections in your codebases.',
    icon: Key,
    articles: [
      { title: 'Node.js client package', href: '/developers/sdks', excerpt: 'Client configuration, authentication, and execution examples.' },
      { title: 'Python SDK client library', href: '/developers/sdks', excerpt: 'Package imports, model selections, and RAG uploads.' },
      { title: 'Go & Rust module guides', href: '/developers/sdks', excerpt: 'Compile client binaries, context pipelines, and error flags.' },
    ],
  },
  {
    title: 'Vector Knowledge Vault',
    desc: 'Upload files and sync vector memory vaults to guide agent voices.',
    icon: Database,
    articles: [
      { title: 'Isolated Vector Vault Security', href: '/legal/security', excerpt: 'How we guarantee tenant data isolation in embeddings indexes.' },
      { title: 'Synchronizing Knowledge PDFs', href: '#', excerpt: 'Best practices for document layout, headings, and semantic context.' },
      { title: 'Supported File Formats', href: '#', excerpt: 'PDF, Markdown, DOCX, and raw text file ingestion limits.' },
    ],
  },
  {
    title: 'Ad Channels Publishing',
    desc: 'Link account credentials and set budget thresholds safety limits.',
    icon: Megaphone,
    articles: [
      { title: 'Authenticating Google Ads', href: '#', excerpt: 'OAuth connection setups, budget boundaries, and developer tokens.' },
      { title: 'Meta Business Suite integrations', href: '#', excerpt: 'Syncing Facebook and Instagram page publication permissions.' },
      { title: 'LinkedIn spec formats', href: '#', excerpt: 'Character counters, draft reviews, and automated image dimensions.' },
    ],
  },
  {
    title: 'Agent Workflows',
    desc: 'Orchestrate branching pathways, triggers, actions, and cost models.',
    icon: GitBranch,
    articles: [
      { title: 'Custom Prompt Variables', href: '/developers/api-docs', excerpt: 'Injecting CRM user attributes dynamically into model contexts.' },
      { title: 'Model Pricing Budget Caps', href: '#', excerpt: 'Defining safety boundaries to throttle cost per agent.' },
      { title: 'Creating Semantic Branches', href: '#', excerpt: 'Setting up flow logic based on copy sentiment evaluations.' },
    ],
  },
];

export default function DocumentationPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = React.useState('');

  const filteredCategories = CATEGORIES.map((cat) => {
    const matchingArticles = cat.articles.filter(
      (art) =>
        art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        art.excerpt.toLowerCase().includes(searchQuery.toLowerCase())
    );
    return { ...cat, articles: matchingArticles };
  }).filter((cat) => cat.articles.length > 0);

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section with Search ────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center space-y-6">
          <FadeUp>
            <SectionLabel>Help Center</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-1 mb-2">
              Documentation & Guides
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-lg mx-auto leading-relaxed mb-6">
              Search articles, explore core concepts, SDK settings, RAG uploads, and ad publishing credentials.
            </p>
          </FadeUp>

          {/* Search Box */}
          <FadeUp delay={0.3} className="max-w-xl mx-auto relative">
            <Search className="absolute left-4 top-3.5 w-5 h-5 text-neutral-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search guides, variables, webhooks..."
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-neutral-900 border border-white/8 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </FadeUp>
        </div>
      </section>

      {/* ─── Categories & Articles list ─────────────────────────────────── */}
      <section className="py-20 max-w-6xl mx-auto px-6 text-left relative z-10">
        {filteredCategories.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            {filteredCategories.map((cat, idx) => {
              const Icon = cat.icon;
              return (
                <FadeUp 
                  key={cat.title} 
                  delay={idx * 0.05}
                  className="p-6 sm:p-8 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-white/10 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center gap-3 border-b border-white/5 pb-4 mb-5">
                      <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-violet-400 shrink-0">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-white leading-tight">{cat.title}</h4>
                        <p className="text-[10px] text-neutral-500 mt-0.5">{cat.desc}</p>
                      </div>
                    </div>

                    <ul className="space-y-4">
                      {cat.articles.map((art) => (
                        <li key={art.title}>
                          <a 
                            href={art.href}
                            className="group block text-xs hover:bg-white/2 p-2 rounded transition-colors"
                          >
                            <span className="font-bold text-neutral-200 group-hover:text-violet-400 transition-colors flex items-center gap-1">
                              {art.title} <ChevronRight className="w-3 h-3 text-neutral-600 group-hover:text-violet-400 group-hover:translate-x-0.5 transition-all" />
                            </span>
                            <p className="text-[10px] text-neutral-500 mt-0.5 leading-relaxed">{art.excerpt}</p>
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                </FadeUp>
              );
            })}
          </div>
        ) : (
          <div className="py-20 text-center text-neutral-500 text-sm flex flex-col items-center gap-3">
            <HelpCircle className="w-8 h-8 opacity-25" />
            <p>No guides match your search query.</p>
          </div>
        )}
      </section>

      {/* ─── Bottom support banner ──────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50 text-center relative overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-violet-600/5 blur-[120px] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <FadeUp>
            <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-4">
              Still Need Help?
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Our engineering support architects are available 24/7/365 to resolve pipeline blockers.
            </p>
            <div className="flex justify-center gap-3">
              <Button 
                variant="violet" 
                size="lg"
                onClick={() => router.push('/company/contact')}
                className="h-11 px-6 text-xs font-semibold"
              >
                Contact Support Desk <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </div>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}
