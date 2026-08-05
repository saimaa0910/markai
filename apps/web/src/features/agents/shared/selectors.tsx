'use client';

import * as React from 'react';
import { usePrompts } from '@/features/prompts/hooks';
import { useCollections, useDocuments } from '@/features/knowledge/hooks';
import { BookOpen, Folder, Database, FileText, Check, Cpu, CheckSquare, Square, Info } from 'lucide-react';
import { cn } from '@eaimos/shared';

// ─────────────────────────────────────────────────────────────────────────────
// Component: PromptSelector
// ─────────────────────────────────────────────────────────────────────────────
interface PromptSelectorProps {
  value: string;
  onChange: (value: string, content: string) => void;
  className?: string;
}

export function PromptSelector({ value, onChange, className }: PromptSelectorProps) {
  const { prompts, isLoading } = usePrompts();
  const [open, setOpen] = React.useState(false);

  const selectedPrompt = prompts.find((p) => p.name === value);

  return (
    <div className={cn('relative', className)}>
      <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block mb-1.5">Bind Prompt Template</label>
      
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between rounded-lg bg-neutral-900 border border-white/8 px-3.5 py-2.5 text-xs text-white hover:bg-neutral-850 hover:border-white/12 transition-all cursor-pointer text-left"
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-violet-400" />
          <span>{selectedPrompt ? selectedPrompt.name : 'Select a Prompt Template...'}</span>
        </div>
        <span className="text-[10px] text-neutral-500">▼</span>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute left-0 right-0 mt-1.5 p-1 bg-neutral-900 border border-white/10 rounded-lg shadow-xl z-20 flex flex-col max-h-60 overflow-y-auto gap-0.5">
            {isLoading ? (
              <span className="text-xs text-neutral-500 p-3 text-center">Loading prompts...</span>
            ) : prompts.length === 0 ? (
              <span className="text-xs text-neutral-500 p-3 text-center">No prompts found</span>
            ) : (
              prompts.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    onChange(p.name, p.content);
                    setOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 rounded text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left"
                >
                  <div>
                    <span className="font-semibold block">{p.name}</span>
                    <span className="text-[10px] text-neutral-500 truncate max-w-[250px] block mt-0.5">{p.content}</span>
                  </div>
                  {value === p.name && <Check className="w-3.5 h-3.5 text-violet-400 shrink-0" />}
                </button>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Component: KnowledgeSelector
// ─────────────────────────────────────────────────────────────────────────────
interface KnowledgeSelectorProps {
  selectedCollections: string[];
  onChangeCollections: (ids: string[]) => void;
  className?: string;
}

export function KnowledgeSelector({
  selectedCollections,
  onChangeCollections,
  className,
}: KnowledgeSelectorProps) {
  const { collections } = useCollections();

  const handleToggleCollection = (id: string) => {
    if (selectedCollections.includes(id)) {
      onChangeCollections(selectedCollections.filter((c) => c !== id));
    } else {
      onChangeCollections([...selectedCollections, id]);
    }
  };

  return (
    <div className={cn('space-y-3.5 text-left', className)}>
      <div>
        <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Vector Collections</label>
        <span className="text-[9px] text-neutral-500 block mt-0.5">Select knowledge collections to inject via semantic search (RAG).</span>
      </div>

      {collections.length === 0 ? (
        <div className="text-xs text-neutral-500 p-4 border border-white/5 bg-neutral-950/40 rounded-lg text-center">No collections found in this workspace</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {collections.map((col) => {
            const isSelected = selectedCollections.includes(col.id);
            return (
              <div
                key={col.id}
                onClick={() => handleToggleCollection(col.id)}
                className={cn(
                  'p-3.5 rounded-xl border cursor-pointer transition-all flex items-start justify-between select-none bg-neutral-950/40',
                  isSelected 
                    ? 'border-violet-500/40 bg-violet-600/5 text-white' 
                    : 'border-white/5 text-neutral-400 hover:border-white/10 hover:bg-neutral-900/10'
                )}
              >
                <div className="flex items-start gap-2.5">
                  <div className="w-8 h-8 rounded bg-neutral-900 border border-white/5 flex items-center justify-center text-violet-400 shrink-0 mt-0.5">
                    <Folder className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold block text-white">{col.name}</span>
                    <span className="text-[10px] text-neutral-500 block mt-0.5">{col.description || 'No description'}</span>
                  </div>
                </div>
                {isSelected ? <CheckSquare className="w-4 h-4 text-violet-400 shrink-0" /> : <Square className="w-4 h-4 text-neutral-600 shrink-0" />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Component: ToolSelector
// ─────────────────────────────────────────────────────────────────────────────
interface ToolSelectorProps {
  allowedTools: string[];
  onChange: (tools: string[]) => void;
  className?: string;
}

const AVAILABLE_TOOLS = [
  { id: 'crm', name: 'CRM Enrichment Integration', desc: 'Allows agents to look up sales pipelines, sync leads, and audit company parameters.' },
  { id: 'campaigns', name: 'Campaign Manager', desc: 'Allows publishing structured copy drafts directly to Google Ads and LinkedIn APIs.' },
  { id: 'search', name: 'Semantic Web Search', desc: 'Instructs agents to run browser queries and lookup target sites descriptions dynamically.' },
  { id: 'email', name: 'Corporate Email Dispatch', desc: 'Grants agents permissions to dispatch outbound cohort sequences and notification digests.' },
  { id: 'webhooks', name: 'Inbound Webhooks API', desc: 'Syncs trigger events directly back to external databases and slack channels.' },
  { id: 'http', name: 'Raw HTTP Requests', desc: 'Allows making custom REST API requests to external platforms and schemas.' },
];

export function ToolSelector({ allowedTools, onChange, className }: ToolSelectorProps) {
  const handleToggleTool = (id: string) => {
    if (allowedTools.includes(id)) {
      onChange(allowedTools.filter((t) => t !== id));
    } else {
      onChange([...allowedTools, id]);
    }
  };

  return (
    <div className={cn('space-y-4 text-left', className)}>
      <div>
        <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Allowed Tools & Functions</label>
        <span className="text-[9px] text-neutral-500 block mt-0.5">Select capabilities for the agent to call during execution steps.</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {AVAILABLE_TOOLS.map((tool) => {
          const isSelected = allowedTools.includes(tool.id);
          return (
            <div
              key={tool.id}
              onClick={() => handleToggleTool(tool.id)}
              className={cn(
                'p-4 rounded-xl border cursor-pointer transition-all flex items-start justify-between select-none bg-neutral-950/40',
                isSelected 
                  ? 'border-violet-500/40 bg-violet-600/5 text-white' 
                  : 'border-white/5 text-neutral-400 hover:border-white/10 hover:bg-neutral-900/10'
              )}
            >
              <div className="space-y-1 pr-4">
                <span className="text-xs font-semibold block text-white">{tool.name}</span>
                <p className="text-[10px] text-neutral-500 leading-relaxed">{tool.desc}</p>
              </div>
              {isSelected ? <CheckSquare className="w-4 h-4 text-violet-400 shrink-0" /> : <Square className="w-4 h-4 text-neutral-600 shrink-0" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Component: MemorySelector
// ─────────────────────────────────────────────────────────────────────────────
interface MemorySelectorProps {
  memoryEnabled: boolean;
  onChangeMemoryEnabled: (enabled: boolean) => void;
  maxMemoryItems: number;
  onChangeMaxMemoryItems: (items: number) => void;
  className?: string;
}

export function MemorySelector({
  memoryEnabled,
  onChangeMemoryEnabled,
  maxMemoryItems,
  onChangeMaxMemoryItems,
  className,
}: MemorySelectorProps) {
  const memoryTypes = [
    { title: 'Conversation Context Retention', desc: 'Retains short-term thread message logs within the session.' },
    { title: 'Organization Knowledge Sync', desc: 'Leverages shared metadata settings from your Viptant team tenant.' },
    { title: 'User Personalization Storage', desc: 'Remembers user preferences across separate runs logs.' },
    { title: 'Brand Vector Identity', desc: 'Restricts tone to strict corporate guidelines in Vault.' },
  ];

  return (
    <div className={cn('space-y-5 text-left', className)}>
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <div>
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Agentic Context Memory</label>
          <span className="text-[9px] text-neutral-500 block mt-0.5">Enable agents to store and access historical contexts dynamically.</span>
        </div>
        
        {/* Toggle Switch */}
        <button
          type="button"
          onClick={() => onChangeMemoryEnabled(!memoryEnabled)}
          className={cn(
            'w-10 h-5.5 rounded-full p-1 transition-colors cursor-pointer outline-none flex items-center',
            memoryEnabled ? 'bg-violet-600' : 'bg-neutral-800 border border-white/5'
          )}
        >
          <div
            className={cn(
              'w-3.5 h-3.5 rounded-full bg-white transition-transform duration-200',
              memoryEnabled ? 'translate-x-4.5' : 'translate-x-0'
            )}
          />
        </button>
      </div>

      {memoryEnabled && (
        <div className="space-y-4 animate-fadeIn">
          {/* Max items slider */}
          <div className="space-y-2 p-4 rounded-xl border border-white/5 bg-neutral-950/20">
            <div className="flex justify-between items-center text-xs">
              <span className="text-neutral-400">Context Window Size (Message Logs)</span>
              <span className="text-violet-400 font-mono font-bold">{maxMemoryItems} turns</span>
            </div>
            <input
              type="range"
              min="5"
              max="50"
              step="5"
              value={maxMemoryItems}
              onChange={(e) => onChangeMaxMemoryItems(parseInt(e.target.value))}
              className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-violet-600"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {memoryTypes.map((m) => (
              <div key={m.title} className="p-3.5 rounded-lg border border-white/5 bg-neutral-950/40 flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-violet-500 shrink-0 mt-1.5" />
                <div>
                  <span className="text-xs font-semibold text-white block">{m.title}</span>
                  <span className="text-[10px] text-neutral-500 block mt-0.5 leading-relaxed">{m.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
