'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Sparkles, ArrowRight, Play, Settings, Bot, Users, Search, Mail } from 'lucide-react';

interface WorkflowTemplate {
  id: string;
  name: string;
  desc: string;
  trigger: string;
  nodesCount: number;
  icon: any;
  color: string;
}

const TEMPLATES: WorkflowTemplate[] = [
  {
    id: 'lead-qualification',
    name: 'Lead Qualification & CRM enrichment',
    desc: 'Automatically enriched pipeline leads using customized agent models and web crawler tools.',
    trigger: 'CRM_EVENT',
    nodesCount: 4,
    icon: Users,
    color: 'from-orange-600/30 to-amber-600/30 border-orange-500/20 text-orange-400',
  },
  {
    id: 'content-generation',
    name: 'Content Generation & Marketing Loop',
    desc: 'Accepts keyword triggers, drafts cohort copy via Agent instructions, and publishes directly to social queues.',
    trigger: 'WEBHOOK',
    nodesCount: 5,
    icon: Bot,
    color: 'from-violet-600/30 to-fuchsia-600/30 border-violet-500/20 text-violet-400',
  },
  {
    id: 'seo-audit',
    name: 'Weekly SEO Audit Report',
    desc: 'Triggered weekly on cron schedules, crawls site domains parameters, runs evaluations, and delivers slack digests.',
    trigger: 'SCHEDULED',
    nodesCount: 3,
    icon: Search,
    color: 'from-blue-600/30 to-indigo-600/30 border-blue-500/20 text-blue-400',
  },
  {
    id: 'email-outreach',
    name: 'Drip Email Campaign Sequence',
    desc: 'Runs contact cohort checks and dispatches personalized email drips depending on customer profile variables.',
    trigger: 'MANUAL',
    nodesCount: 4,
    icon: Mail,
    color: 'from-emerald-600/30 to-teal-600/30 border-emerald-500/20 text-emerald-400',
  },
];

export default function WorkflowTemplatesPage() {
  const router = useRouter();

  const handleUseTemplate = (template: WorkflowTemplate) => {
    router.push(
      `/dashboard/workflows/create?name=${encodeURIComponent(template.name)}&desc=${encodeURIComponent(template.desc)}&trigger=${template.trigger}`
    );
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-white/5 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-400" /> Pre-built Automation Templates
        </h2>
        <p className="text-xs text-neutral-400 mt-1">
          Quickstart campaign loops, lead sync pipelines, and data routers.
        </p>
      </div>

      {/* Grid List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {TEMPLATES.map((tmpl) => {
          const Icon = tmpl.icon;
          return (
            <div 
              key={tmpl.id}
              className="group p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/25 hover:bg-neutral-900/10 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start mb-4">
                  <span className={`text-[9px] font-bold px-2.5 py-0.5 rounded border inline-block bg-gradient-to-tr ${tmpl.color}`}>
                    {tmpl.trigger}
                  </span>
                  <span className="text-[10px] text-neutral-500 font-mono">
                    {tmpl.nodesCount} step nodes
                  </span>
                </div>

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
