'use client';

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAgents } from '@/features/agents/hooks';
import { useModels } from '@/features/ai-platform/hooks';
import { AgentDefinition, AgentType } from '@/features/agents/types';
import { PromptSelector, KnowledgeSelector, ToolSelector, MemorySelector } from '@/features/agents/components/selectors';
import { Button } from '@/components/ui/button';
import { 
  Bot, Settings, Sparkles, Folder, Play, CheckCircle2, ChevronRight, 
  ArrowLeft, Cpu, ShieldCheck, Database, HelpCircle 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

const STEPS = [
  { id: 1, label: 'Identity', desc: 'Basic info & tags' },
  { id: 2, label: 'LLM Model', desc: 'Model parameters' },
  { id: 3, label: 'RAG Knowledge', desc: 'Embeddings sync' },
  { id: 4, label: 'Memory', desc: 'Context windows' },
  { id: 5, label: 'Capabilities', desc: 'Allowed tools' },
  { id: 6, label: 'Review', desc: 'Deploy definition' },
];

export default function CreateAgentWizardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const templateName = searchParams.get('name') || '';
  const templateType = (searchParams.get('type') as AgentType) || 'CUSTOM';
  const templatePrompt = searchParams.get('prompt') || '';
  const templateTools = searchParams.get('tools') ? searchParams.get('tools')!.split(',') : [];

  const { createAgent } = useAgents();
  const { models } = useModels();

  // Wizard state step tracker
  const [step, setStep] = React.useState(1);

  // Form inputs
  const [name, setName] = React.useState(templateName);
  const [description, setDescription] = React.useState('');
  const [avatarColor, setAvatarColor] = React.useState('violet');
  const [agentType, setAgentType] = React.useState<AgentType>(templateType);
  const [preferredModel, setPreferredModel] = React.useState('');
  const [temperature, setTemperature] = React.useState(0.7);
  const [systemPrompt, setSystemPrompt] = React.useState(templatePrompt);
  const [selectedCollections, setSelectedCollections] = React.useState<string[]>([]);
  const [memoryEnabled, setMemoryEnabled] = React.useState(true);
  const [maxMemoryItems, setMaxMemoryItems] = React.useState(20);
  const [allowedTools, setAllowedTools] = React.useState<string[]>(templateTools);

  // Auto-select first model if available
  React.useEffect(() => {
    if (models.length > 0 && !preferredModel) {
      setPreferredModel(models[0].name || models[0].id);
    }
  }, [models, preferredModel]);

  const handleNext = () => {
    if (step < 6) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleDeploy = () => {
    createAgent.mutate(
      {
        name,
        description: description || null,
        agent_type: agentType,
        status: 'ACTIVE',
        system_prompt: systemPrompt || null,
        prompt_template_name: null,
        allowed_tools: allowedTools,
        preferred_model: preferredModel || null,
        temperature,
        max_tokens: 1500,
        memory_enabled: memoryEnabled,
        max_memory_items: maxMemoryItems,
        max_iterations: 10,
        is_public: false,
        avatar_color: avatarColor,
      },
      {
        onSuccess: () => {
          router.push('/dashboard/agents');
        },
      }
    );
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto">
      {/* Header toolbar */}
      <div className="flex items-center gap-3 border-b border-white/5 pb-4">
        <button
          onClick={() => router.push('/dashboard/agents')}
          className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-neutral-400 hover:text-white transition-all cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Create AI Agent</h2>
          <p className="text-xs text-neutral-400 mt-1">Configure identity, LLM triggers, memories, and capabilities.</p>
        </div>
      </div>

      {/* Horizontal Multi-step Stepper */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 bg-neutral-950/40 p-3 rounded-xl border border-white/5 select-none">
        {STEPS.map((s) => (
          <div 
            key={s.id} 
            className={cn(
              'p-2.5 rounded-lg border text-left transition-all',
              step === s.id 
                ? 'border-violet-500 bg-violet-600/5 text-white' 
                : step > s.id 
                ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400'
                : 'border-transparent text-neutral-500'
            )}
          >
            <span className="text-[10px] font-mono font-bold block uppercase tracking-wider">Step 0{s.id}</span>
            <span className="text-xs font-semibold block mt-1">{s.label}</span>
          </div>
        ))}
      </div>

      {/* Wizard Form Panels */}
      <div className="p-6 rounded-2xl border border-white/10 bg-neutral-950/40 min-h-[350px] flex flex-col justify-between glass">
        
        <div className="space-y-6">
          {/* STEP 1: Basic Identity */}
          {step === 1 && (
            <div className="space-y-4 animate-fadeIn">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Agent Name *</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Lead Enrichment Copywriter..."
                    className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Agent Classification *</label>
                  <select
                    value={agentType}
                    onChange={(e) => setAgentType(e.target.value as AgentType)}
                    className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 transition-colors"
                  >
                    <option value="CRM">CRM & Operations</option>
                    <option value="CONTENT">Content Studio</option>
                    <option value="MARKETING">Marketing & Creative</option>
                    <option value="CAMPAIGN">Campaign Orchestration</option>
                    <option value="RESEARCH">Semantic Research</option>
                    <option value="CUSTOM">Custom Builder</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Description & Instructions Summary</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="Outline the operational targets and bounds of this agent configuration..."
                  className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors leading-relaxed"
                />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Avatar Color Badge</label>
                <div className="flex gap-2.5">
                  {['violet', 'blue', 'emerald', 'rose', 'amber', 'cyan'].map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setAvatarColor(color)}
                      className={cn(
                        'w-7 h-7 rounded-full border transition-all cursor-pointer flex items-center justify-center',
                        color === 'violet' ? 'bg-violet-600 border-violet-500' :
                        color === 'blue' ? 'bg-blue-600 border-blue-500' :
                        color === 'emerald' ? 'bg-emerald-600 border-emerald-500' :
                        color === 'rose' ? 'bg-rose-600 border-rose-500' :
                        color === 'amber' ? 'bg-amber-600 border-amber-500' : 'bg-cyan-600 border-cyan-500',
                        avatarColor === color ? 'ring-2 ring-white/50 border-white' : 'border-transparent opacity-60'
                      )}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: AI Configuration */}
          {step === 2 && (
            <div className="space-y-5 animate-fadeIn">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Preferred LLM Model *</label>
                  <select
                    value={preferredModel}
                    onChange={(e) => setPreferredModel(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none focus:border-violet-500 transition-colors font-mono"
                  >
                    {models.map((m) => (
                      <option key={m.id} value={m.name || m.id}>{m.name || m.id}</option>
                    ))}
                    {models.length === 0 && <option value="">No models available (Gateway default)</option>}
                  </select>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center text-[10px] font-bold text-neutral-400 uppercase tracking-wider">
                    <span>Model Temperature</span>
                    <span className="text-violet-400 font-mono">{temperature}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-violet-600 mt-2.5"
                  />
                </div>
              </div>

              {/* Prompt selection dropdown utility */}
              <PromptSelector 
                value="" 
                onChange={(name, content) => {
                  setSystemPrompt(content);
                }} 
              />

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">System Instructions Prompt *</label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={5}
                  placeholder="e.g. You are a professional copywriter. Adhere to brand guidelines context..."
                  className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors font-mono leading-relaxed"
                />
              </div>
            </div>
          )}

          {/* STEP 3: Knowledge (RAG) */}
          {step === 3 && (
            <div className="animate-fadeIn">
              <KnowledgeSelector
                selectedCollections={selectedCollections}
                onChangeCollections={setSelectedCollections}
              />
            </div>
          )}

          {/* STEP 4: Memory Settings */}
          {step === 4 && (
            <div className="animate-fadeIn">
              <MemorySelector
                memoryEnabled={memoryEnabled}
                onChangeMemoryEnabled={setMemoryEnabled}
                maxMemoryItems={maxMemoryItems}
                onChangeMaxMemoryItems={setMaxMemoryItems}
              />
            </div>
          )}

          {/* STEP 5: Allowed Tools */}
          {step === 5 && (
            <div className="animate-fadeIn">
              <ToolSelector
                allowedTools={allowedTools}
                onChange={setAllowedTools}
              />
            </div>
          )}

          {/* STEP 6: Review Summary */}
          {step === 6 && (
            <div className="space-y-6 text-xs leading-relaxed animate-fadeIn">
              <div>
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">Review and Deploy</span>
                <span className="text-neutral-400 mt-1 block">Verify parameters before committing agent definition.</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-white/5 pt-5 text-left font-mono">
                <div className="space-y-3">
                  <div className="flex justify-between"><span className="text-neutral-500">Agent Name:</span> <span className="text-white font-bold">{name || 'Unnamed Agent'}</span></div>
                  <div className="flex justify-between"><span className="text-neutral-500">Classification:</span> <span className="text-white uppercase">{agentType}</span></div>
                  <div className="flex justify-between"><span className="text-neutral-500">Model Route:</span> <span className="text-white">{preferredModel || 'Gateway Default'}</span></div>
                  <div className="flex justify-between"><span className="text-neutral-500">Temperature:</span> <span className="text-white">{temperature}</span></div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between"><span className="text-neutral-500">Allowed Tools:</span> <span className="text-white">{allowedTools.length > 0 ? allowedTools.join(', ') : 'None'}</span></div>
                  <div className="flex justify-between"><span className="text-neutral-500">Memory Sync:</span> <span className="text-white">{memoryEnabled ? `Yes (${maxMemoryItems} turns)` : 'Disabled'}</span></div>
                  <div className="flex justify-between"><span className="text-neutral-500">RAG Indexes:</span> <span className="text-white">{selectedCollections.length} collections linked</span></div>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-neutral-900 border border-white/5 text-left">
                <span className="text-[9px] text-neutral-500 uppercase tracking-wider block font-bold mb-1">BOUND SYSTEM PROMPT</span>
                <p className="text-[10px] text-neutral-300 truncate max-w-full font-mono">{systemPrompt || 'No prompt instructions provided.'}</p>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Action Buttons */}
        <div className="flex justify-between border-t border-white/5 pt-6 mt-10">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={step === 1}
            className="h-9 px-4 text-xs text-neutral-400 border-white/5 cursor-pointer"
          >
            Back
          </Button>

          {step === 6 ? (
            <Button
              variant="violet"
              onClick={handleDeploy}
              disabled={!name.trim() || !systemPrompt.trim()}
              className="h-9 px-5 text-xs font-semibold gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" /> Deploy Agent
            </Button>
          ) : (
            <Button
              variant="violet"
              onClick={handleNext}
              disabled={step === 1 && !name.trim()}
              className="h-9 px-5 text-xs font-semibold gap-1.5"
            >
              Continue <ChevronRight className="w-4 h-4" />
            </Button>
          )}
        </div>

      </div>
    </div>
  );
}
