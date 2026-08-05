'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/services/api-client';
import { Bot, Sparkles, Megaphone, Search, Users, Cpu, ArrowRight, Share2 } from 'lucide-react';

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
    id: 'content-agent',
    name: 'Content Agent',
    desc: 'Generates high-converting marketing collateral, blogs, landing pages, emails, social posts, ads, brand voice alignment, and video scripts.',
    agentType: 'CONTENT',
    tools: ['knowledge_tool', 'prompt_tool'],
    systemPrompt: 'You are the Viptant Content Agent. You specialize in creating high-quality, SEO-optimized, brand-aligned marketing collateral including blogs, landing pages, email copy, and social posts. Always maintain the organization\'s brand voice and tone guidelines.',
    icon: Bot,
    color: 'from-orange-600/30 to-amber-600/30 border-orange-500/20 text-orange-400',
  },
  {
    id: 'seo-agent',
    name: 'SEO Agent',
    desc: 'Performs keyword research, SERP analysis, topic clustering, SEO audits, meta tag generation, and content optimization recommendations.',
    agentType: 'SEO',
    tools: ['web_search_tool', 'knowledge_tool'],
    systemPrompt: 'You are the Viptant SEO Agent. Your goal is to maximize organic search visibility. Audit the user\'s content, perform search query research, identify SERP trends, compile topic clusters, and draft high-performance meta tags.',
    icon: Search,
    color: 'from-blue-600/30 to-indigo-600/30 border-blue-500/20 text-blue-400',
  },
  {
    id: 'campaign-agent',
    name: 'Campaign Agent',
    desc: 'Orchestrates end-to-end multi-channel marketing campaigns, design A/B testing, and campaign copy variations across channels.',
    agentType: 'CAMPAIGN',
    tools: ['campaign_tool', 'web_search_tool'],
    systemPrompt: 'You are the Viptant Campaign Agent. You analyze performance data, coordinate multichannels, design A/B tests, recommend budget allocations, and automate promotional messaging.',
    icon: Megaphone,
    color: 'from-emerald-600/30 to-teal-600/30 border-emerald-500/20 text-emerald-400',
  },
  {
    id: 'social-media-agent',
    name: 'Social Media Agent',
    desc: 'Plans, generates, optimizes, schedules, and publishes content across 14 social media platforms.',
    agentType: 'SOCIAL',
    tools: ['knowledge_tool', 'image_generation_tool', 'campaign_tool', 'analytics_tool', 'brand_tool', 'web_search_tool', 'email_tool', 'calendar_tool'],
    systemPrompt: 'You are the Viptant Social Media Agent. You specialize in generating platform-optimized posts, threads, stories, and community content. You orchestrate caption writing, image generation, hashtag selection, and calendar scheduling.',
    icon: Share2,
    color: 'from-sky-600/30 to-blue-600/30 border-sky-500/20 text-sky-400',
  },
];

export default function AgentTemplatesPage() {
  const router = useRouter();
  const [apiTemplates, setApiTemplates] = React.useState<Template[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    apiClient.get('/agents/templates')
      .then((res) => {
        if (Array.isArray(res.data)) {
          const mapped = res.data.map((item: any) => {
            const base = TEMPLATES.find((t) => t.name.toLowerCase() === item.name.toLowerCase());
            return {
              id: item.name.toLowerCase().replace(/ /g, '-'),
              name: item.name,
              desc: item.description,
              agentType: item.agent_type,
              tools: item.allowed_tools || [],
              systemPrompt: item.system_prompt || '',
              icon: base?.icon || Bot,
              color: base?.color || 'from-violet-600/30 to-fuchsia-600/30 border-violet-500/20 text-violet-400',
            };
          });
          setApiTemplates(mapped);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const displayTemplates = apiTemplates.length > 0 ? apiTemplates : TEMPLATES;

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
        {displayTemplates.map((tmpl, idx) => {
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
