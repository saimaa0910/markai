import * as React from 'react';
import { usePrompts } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { 
  Save, Eye, Code, FileText, Sparkles, Sliders, Info, 
  HelpCircle, Variable, DollarSign, Clock, ArrowLeft 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

export function EditorPage() {
  const { createPrompt } = usePrompts();

  const [promptName, setPromptName] = React.useState('');
  const [content, setContent] = React.useState('');
  const [category, setCategory] = React.useState('Marketing');
  const [tagsInput, setTagsInput] = React.useState('');
  
  const [previewValues, setPreviewValues] = React.useState<Record<string, string>>({});
  const [activeViewTab, setActiveViewTab] = React.useState<'raw' | 'preview'>('raw');

  // Parse variables dynamically from content
  const detectedVars = React.useMemo(() => {
    const matches = content.match(/\{\{([^}]+)\}\}/g);
    const unique = matches ? [...new Set(matches.map((m) => m.replace(/[{}]/g, '').trim()))] : [];
    
    // Initialize preview values for newly found variables
    setPreviewValues((prev) => {
      const next = { ...prev };
      unique.forEach((v) => {
        if (next[v] === undefined) next[v] = '';
      });
      return next;
    });

    return unique;
  }, [content]);

  // Compute metrics
  const stats = React.useMemo(() => {
    const chars = content.length;
    const words = content.trim().split(/\s+/).filter(Boolean).length;
    const tokens = Math.round(chars / 4.2);
    const cost = tokens * 0.0000015; // $0.0015 per 1K tokens
    return { chars, words, tokens, cost };
  }, [content]);

  const handleSave = () => {
    if (!promptName.trim()) {
      toast.error('Invalid Name', 'Prompt template name cannot be empty.');
      return;
    }
    if (!content.trim()) {
      toast.error('Invalid content', 'Prompt instruction payload content cannot be empty.');
      return;
    }

    createPrompt.mutate({
      name: promptName,
      content,
      category,
      tags: tagsInput ? tagsInput.split(',').map((t) => t.trim()) : [],
      is_shared: true,
      version: 1,
    }, {
      onSuccess: () => {
        toast.success('Prompt Saved', `Released template ${promptName} v1 successfully.`);
        setPromptName('');
        setContent('');
        setTagsInput('');
        setPreviewValues({});
      },
      onError: () => {
        toast.error('Save Failed', 'Could not register prompt template.');
      }
    });
  };

  // Compile prompt for preview output
  const compiledPreview = React.useMemo(() => {
    let rendered = content;
    detectedVars.forEach((v) => {
      const val = previewValues[v] || `[${v}]`;
      rendered = rendered.replace(new RegExp(`\\{\\{\\s*${v}\\s*\\}\\}`, 'g'), val);
    });
    return rendered;
  }, [content, detectedVars, previewValues]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors">
        <a href="/dashboard/prompts" className="inline-flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </a>
      </div>

      <PageHeader
        title="Prompt Editor Workspace"
        description="Write LLM prompt instructions with dynamic variables. View estimated token usage and costs."
        icon={<Code className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Workspace editor</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* MONACO TEXT AREA WORKSPACE (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <Card className="p-4 flex flex-col gap-4">
            
            {/* Editor Top Bar controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <Input
                  placeholder="e.g. email_welcome_template"
                  value={promptName}
                  onChange={(e) => setPromptName(e.target.value)}
                  className="bg-neutral-950/40 border-white/5 h-8 text-xs font-semibold w-48 sm:w-64"
                />
              </div>

              <div className="flex items-center bg-neutral-900 border border-white/5 rounded p-0.5 text-[10px] font-semibold">
                <button
                  onClick={() => setActiveViewTab('raw')}
                  className={`px-3 py-1 rounded transition-all cursor-pointer ${
                    activeViewTab === 'raw' ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Code Editor
                </button>
                <button
                  onClick={() => setActiveViewTab('preview')}
                  className={`px-3 py-1 rounded transition-all cursor-pointer ${
                    activeViewTab === 'preview' ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Compiled Preview
                </button>
              </div>
            </div>

            {/* Content area */}
            {activeViewTab === 'raw' ? (
              <div className="relative">
                {/* Simulated Monaco Editor wrapper */}
                <div className="p-4 bg-black/40 border border-white/5 rounded-xl font-mono text-xs text-neutral-300 leading-relaxed min-h-[250px] relative overflow-hidden flex">
                  {/* Line Numbers */}
                  <div className="w-8 select-none text-neutral-600 text-right pr-3 border-r border-white/5 flex flex-col gap-0.5 pointer-events-none">
                    {Array.from({ length: Math.max(1, content.split('\n').length) }).map((_, idx) => (
                      <div key={idx}>{idx + 1}</div>
                    ))}
                  </div>
                  {/* Textarea Input */}
                  <textarea
                    placeholder="Enter prompt instructions. Add custom parameters matching {{variable}} tag parameters."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="flex-1 bg-transparent border-0 outline-none pl-3 resize-none w-full min-h-[240px] focus:ring-0 text-white font-mono leading-relaxed"
                  />
                </div>
              </div>
            ) : (
              <div className="p-4 bg-black/40 border border-white/5 rounded-xl font-mono text-xs text-neutral-300 leading-relaxed min-h-[250px] whitespace-pre-wrap">
                {compiledPreview}
              </div>
            )}

            {/* Bottom Actions and Attributes */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-white/5 pt-4 mt-1 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="text-[9px] text-neutral-400 font-bold uppercase">Category</label>
                <Select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="bg-neutral-950 border-white/5 h-8 text-[11px]"
                  options={[
                    { label: 'Marketing', value: 'Marketing' },
                    { label: 'CRM', value: 'CRM' },
                    { label: 'Ads', value: 'Ads' },
                  ]}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[9px] text-neutral-400 font-bold uppercase">Tags (comma-separated)</label>
                <Input
                  placeholder="e.g. email, user"
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  className="bg-neutral-950/40 border-white/5 h-8 text-[11px]"
                />
              </div>
            </div>

            <div className="border-t border-white/5 pt-3.5 flex justify-end">
              <Button variant="violet" size="sm" onClick={handleSave} className="text-xs h-8">
                <Save className="w-3.5 h-3.5 mr-1" />
                Release Prompt v1
              </Button>
            </div>
          </Card>
        </div>

        {/* SIDEBAR PARAMETERS & VARIABLES (Right 1 column) */}
        <div className="flex flex-col gap-4">
          {/* Estimated Token metrics */}
          <Card className="p-4 bg-neutral-950/20 flex flex-col gap-4 text-xs font-mono">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-violet-400" /> Token Estimation
            </span>

            <div className="flex flex-col gap-3">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Characters:</span>
                <span className="text-white font-bold">{stats.chars}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Estimated Tokens:</span>
                <span className="text-white font-bold">{stats.tokens} t</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Estimated Cost:</span>
                <span className="text-emerald-400 font-bold">${stats.cost.toFixed(6)}</span>
              </div>
            </div>
          </Card>

          {/* Variables Value Mappings */}
          <Card className="flex flex-col gap-4">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Variable className="w-3.5 h-3.5 text-violet-400" /> Variables Mapping
            </span>

            <div className="flex flex-col gap-3.5">
              {detectedVars.map((v) => (
                <div key={v} className="flex flex-col gap-1.5 text-xs">
                  <span className="font-bold text-white font-mono text-[10px]">{`{{${v}}}`}</span>
                  <Input
                    placeholder="Enter placeholder value..."
                    value={previewValues[v] || ''}
                    onChange={(e) => setPreviewValues({ ...previewValues, [v]: e.target.value })}
                    className="bg-neutral-950/40 border-white/5 h-8 text-[11px]"
                  />
                </div>
              ))}

              {detectedVars.length === 0 && (
                <div className="py-12 flex flex-col items-center justify-center text-center text-neutral-600">
                  <Variable className="w-6 h-6 mb-1 text-neutral-700" />
                  <span className="text-[10px] font-semibold">No variables detected</span>
                  <p className="text-[9px] text-neutral-500 mt-0.5 max-w-[150px]">
                    Use tag parameter brackets to declare input fields.
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
export { HelpCircle, DollarSign, Clock };
