'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAgents } from '@/features/agents/hooks';
import { AgentDefinition } from '@/features/agents/types';
import { Button } from '@/components/ui/button';
import { AgentAvatar } from '@/features/agents/components/badges';
import { 
  Sparkles, Search, ArrowRight, Download, Upload, 
  Share2, Play, Star, Copy, Library, RefreshCw 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

interface MarketplaceAgent {
  id: string;
  name: string;
  desc: string;
  category: string;
  rating: number;
  installs: number;
  author: string;
  avatarColor: string;
}

const FEATURED: MarketplaceAgent[] = [
  { id: 'm1', name: 'SPF/DKIM Auditor', desc: 'Validates workspace domain DNS settings, SPF, and DKIM public records.', category: 'CRM', rating: 4.9, installs: 1240, author: 'Viptant Labs', avatarColor: 'violet' },
  { id: 'm2', name: 'Google Ads Generator', desc: 'Drafts brand-aligned creative copy options filterable by campaign target keywords.', category: 'CONTENT', rating: 4.8, installs: 3820, author: 'Creative AI', avatarColor: 'emerald' },
  { id: 'm3', name: 'SEO Competitor Auditor', desc: 'Queries Google search results, audits top-ranking headers, and drafts SEO maps.', category: 'RESEARCH', rating: 4.7, installs: 940, author: 'SEO Suite', avatarColor: 'blue' },
];

export default function AgentMarketplacePage() {
  const router = useRouter();
  const { agents, createAgent } = useAgents(1, 100);

  const [search, setSearch] = React.useState('');
  const [filterCategory, setFilterCategory] = React.useState('ALL');
  const [activeTab, setActiveTab] = React.useState<'featured' | 'org' | 'community'>('featured');

  const handleClone = (name: string, desc: string, type: any, prompt: string) => {
    createAgent.mutate(
      {
        name: `${name} (Cloned)`,
        description: desc,
        agent_type: type,
        status: 'ACTIVE',
        system_prompt: prompt,
        prompt_template_name: null,
        allowed_tools: ['search'],
        preferred_model: 'gemini-2.5-pro',
        temperature: 0.7,
        max_tokens: 1000,
        memory_enabled: true,
        max_memory_items: 20,
        max_iterations: 10,
        is_public: false,
        avatar_color: 'violet',
      },
      {
        onSuccess: () => {
          alert('Agent cloned to your library successfully!');
          router.push('/dashboard/agents');
        },
      }
    );
  };

  const handleExport = (agent: any) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(agent, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${agent.name.toLowerCase().replace(/ /g, '_')}_definition.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        createAgent.mutate(
          {
            name: parsed.name || 'Imported Agent',
            description: parsed.description || 'Imported definition.',
            agent_type: parsed.agent_type || 'CUSTOM',
            status: 'ACTIVE',
            system_prompt: parsed.system_prompt || 'You are an assistant.',
            prompt_template_name: null,
            allowed_tools: parsed.allowed_tools || [],
            preferred_model: parsed.preferred_model || 'gemini-2.5-pro',
            temperature: parsed.temperature || 0.7,
            max_tokens: parsed.max_tokens || 1000,
            memory_enabled: parsed.memory_enabled !== false,
            max_memory_items: parsed.max_memory_items || 20,
            max_iterations: parsed.max_iterations || 10,
            is_public: false,
            avatar_color: parsed.avatar_color || 'violet',
          },
          {
            onSuccess: () => {
              alert('Agent definition imported successfully!');
              router.push('/dashboard/agents');
            },
          }
        );
      } catch (err) {
        alert('Failed to parse agent definition JSON.');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Library className="w-5 h-5 text-violet-400" /> Agent Marketplace
          </h2>
          <p className="text-xs text-neutral-400 mt-1">
            Install custom community blueprints, export definitions, or clone private organization configurations.
          </p>
        </div>

        <div className="flex gap-2">
          {/* Import file input helper */}
          <label className="h-10 px-4 rounded-lg border border-white/5 bg-neutral-900 text-neutral-300 hover:text-white flex items-center gap-1.5 text-xs font-semibold cursor-pointer select-none">
            <Upload className="w-4 h-4" /> Import Agent
            <input type="file" accept=".json" onChange={handleImport} className="hidden" />
          </label>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex justify-between items-center bg-neutral-950/40 p-3 rounded-xl border border-white/5 gap-4">
        <div className="flex bg-neutral-900 rounded border border-white/5 p-0.5 shrink-0 select-none">
          {(['featured', 'org', 'community'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-4 py-1.5 rounded text-[10px] font-bold tracking-wide transition-colors cursor-pointer capitalize',
                activeTab === tab ? 'bg-neutral-800 text-white' : 'text-neutral-500 hover:text-neutral-300'
              )}
            >
              {tab === 'org' ? 'Organization Private' : tab}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-1 max-w-xs">
          <Search className="w-4 h-4 text-neutral-500 shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search marketplace..."
            className="w-full bg-transparent border-0 text-xs text-white placeholder-neutral-600 focus:outline-none"
          />
        </div>
      </div>

      {/* Rendering blocks */}
      {activeTab === 'featured' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FEATURED.filter((f) => f.name.toLowerCase().includes(search.toLowerCase())).map((agent) => (
            <div key={agent.id} className="group p-5 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/30 transition-all flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-4">
                  <span className="text-[8px] font-mono font-bold px-2 py-0.5 rounded border border-white/5 text-neutral-500 uppercase">
                    {agent.category}
                  </span>
                  <div className="flex items-center gap-1 text-[10px] text-amber-400 font-bold font-mono">
                    <Star className="w-3.5 h-3.5 fill-amber-400 stroke-transparent" />
                    <span>{agent.rating}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 mb-3">
                  <AgentAvatar name={agent.name} avatarColor={agent.avatarColor} size="sm" />
                  <div>
                    <h4 className="text-sm font-bold text-white leading-tight group-hover:text-violet-300 transition-colors">{agent.name}</h4>
                    <span className="text-[9px] text-neutral-600 block mt-0.5">by {agent.author}</span>
                  </div>
                </div>

                <p className="text-neutral-400 text-xs leading-relaxed mb-6 min-h-[36px] line-clamp-2">
                  {agent.desc}
                </p>
              </div>

              <div className="border-t border-white/5 pt-4 mt-auto flex gap-2">
                <Button
                  variant="violet"
                  onClick={() => handleClone(agent.name, agent.desc, agent.category, `You are a specialized ${agent.name} assistant.`)}
                  className="flex-1 h-9 text-xs font-semibold gap-1.5"
                >
                  <Copy className="w-3.5 h-3.5" /> Install Agent
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleExport({ name: agent.name, description: agent.desc, agent_type: agent.category, system_prompt: `You are a specialized ${agent.name} assistant.`, allowed_tools: ['search'] })}
                  className="h-9 w-9 p-0 border-white/5"
                  title="Export Config"
                >
                  <Download className="w-4 h-4 text-neutral-400" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'org' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {agents.filter((a) => a.name.toLowerCase().includes(search.toLowerCase())).map((ag) => (
            <div key={ag.id} className="group p-5 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/30 transition-all flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-4">
                  <span className="text-[8px] font-mono font-bold px-2 py-0.5 rounded border border-white/5 text-neutral-500 uppercase">
                    {ag.agent_type}
                  </span>
                  <span className="text-[8px] font-mono text-neutral-600">Private Org</span>
                </div>

                <div className="flex items-center gap-3 mb-3">
                  <AgentAvatar name={ag.name} avatarColor={ag.avatar_color} size="sm" />
                  <div>
                    <h4 className="text-sm font-bold text-white leading-tight group-hover:text-violet-300 transition-colors">{ag.name}</h4>
                  </div>
                </div>

                <p className="text-neutral-400 text-xs leading-relaxed mb-6 min-h-[36px] line-clamp-2">
                  {ag.description || 'No description provided.'}
                </p>
              </div>

              <div className="border-t border-white/5 pt-4 mt-auto flex gap-2">
                <Button
                  variant="violet"
                  onClick={() => handleClone(ag.name, ag.description || '', ag.agent_type, ag.system_prompt || '')}
                  className="flex-1 h-9 text-xs font-semibold gap-1.5"
                >
                  <Copy className="w-3.5 h-3.5" /> Clone Agent
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleExport(ag)}
                  className="h-9 w-9 p-0 border-white/5"
                  title="Export Config"
                >
                  <Download className="w-4 h-4 text-neutral-400" />
                </Button>
              </div>
            </div>
          ))}
          {agents.length === 0 && (
            <span className="text-xs text-neutral-500 block p-8 text-center col-span-3">No custom agents found in this organization.</span>
          )}
        </div>
      )}

      {activeTab === 'community' && (
        <div className="py-20 text-center text-neutral-500 border border-dashed border-white/8 rounded-2xl bg-neutral-950/20 flex flex-col items-center justify-center p-4 gap-2">
          <Sparkles className="w-8 h-8 opacity-20" />
          <span className="text-xs">Community Repository coming soon. Check Featured and Org tabs for active items.</span>
        </div>
      )}

    </div>
  );
}
