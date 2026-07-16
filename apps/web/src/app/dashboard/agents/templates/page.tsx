'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { Bot, Sparkles, Megaphone, Search, Users, Cpu, ArrowRight } from 'lucide-react';

interface Template {
  id: string;
  name: string;
  desc: string;
  agentType: string;
  tools: string[];
  systemPrompt: string;
  icon: any;
  color: string;
}

const TEMPLATES: Template[] = [
  {
    id: 'lead-profiler',
    name: 'Lead Profiler Agent',
    desc: 'Automatically enriches sales contacts by scraping details and looking up corporate structures.',
    agentType: 'CRM',
    tools: ['crm', 'search'],
    systemPrompt: 'You are an advanced B2B lead enrichment agent. Scrape website profiles and identify corporate parameters.',
    icon: Users,
    color: 'from-orange-600/30 to-amber-600/30 border-orange-500/20 text-orange-400',
  },
  {
    id: 'seo-optimizer',
    name: 'SEO Optimizer Assistant',
    desc: 'Audits blog drafts semantically and injects active keyword tags to boost search indexing.',
    agentType: 'RESEARCH',
    tools: ['search', 'http'],
    systemPrompt: 'You are an expert SEO auditor. Analyze blog drafts, cross-reference competitor structures, and suggest keyword insertions.',
    icon: Search,
    color: 'from-blue-600/30 to-indigo-600/30 border-blue-500/20 text-blue-400',
  },
  {
    id: 'outreach-writer',
    name: 'Campaign Outreach Writer',
    desc: 'Drafts brand-aligned marketing emails and generates Google Ads copy variations autonomously.',
    agentType: 'CONTENT',
    tools: ['email', 'campaigns'],
    systemPrompt: 'You are a conversion-focused copywriting agent. Draft email sequences matching our brand voice guidelines.',
    icon: Megaphone,
    color: 'from-emerald-600/30 to-teal-600/30 border-emerald-500/20 text-emerald-400',
  },
];

export default function AgentTemplatesPage() {
  const router = useRouter();

  const handleUseTemplate = (template: Template) => {
    // Route to wizard passing details in query parameter
    router.push(
      `/dashboard/agents/create?name=${encodeURIComponent(template.name)}&type=${template.agentType}&prompt=${encodeURIComponent(template.systemPrompt)}&tools=${template.tools.join(',')}`
    );
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-white/5 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-400" /> Template Gallery
        </h2>
        <p className="text-xs text-neutral-400 mt-1">
          Launch pre-built agent definitions optimized for common marketing tasks.
        </p>
      </div>

      {/* Templates List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {TEMPLATES.map((tmpl, idx) => {
          const Icon = tmpl.icon;
          return (
            <div 
              key={tmpl.id}
              className="group p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/25 hover:bg-neutral-900/10 transition-all flex flex-col justify-between"
            >
              <div>
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded border inline-block mb-4 bg-gradient-to-tr ${tmpl.color}`}>
                  {tmpl.agentType}
                </span>
                
                <h4 className="text-base font-bold text-white mb-2 leading-snug group-hover:text-violet-300 transition-colors">
                  {tmpl.name}
                </h4>
                
                <p className="text-neutral-400 text-xs leading-relaxed mb-6">
                  {tmpl.desc}
                </p>
              </div>

              <div className="border-t border-white/5 pt-4 mt-auto">
                <Button
                  variant="violet"
                  onClick={() => handleUseTemplate(tmpl)}
                  className="w-full h-9 text-xs font-semibold gap-1.5"
                >
                  Use Template <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
