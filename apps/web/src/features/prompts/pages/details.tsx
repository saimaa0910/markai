import * as React from 'react';
import { usePrompt } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  BookOpen, Edit3, ArrowLeft, Copy, Cpu, 
  HelpCircle, Settings, Play, Sliders, Calendar, User, Info 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';

interface PromptDetailsPageProps {
  id: string; // Refers to the name family
}

export function PromptDetailsPage({ id }: PromptDetailsPageProps) {
  // Grab prompt latest version details by family name
  const { prompt } = usePrompt(id);

  if (!prompt) {
    return (
      <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
        <BookOpen className="w-10 h-10 text-neutral-600" />
        <h4 className="font-bold text-white text-sm">Prompt Template Not Found</h4>
        <a href="/dashboard/prompts">
          <Button variant="outline" size="sm" className="border-white/5">
            Back to Dashboard
          </Button>
        </a>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(prompt.content);
    toast.success('Prompt Content Copied');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors">
        <a href="/dashboard/prompts/library" className="inline-flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Library
        </a>
      </div>

      <PageHeader
        title={prompt.name}
        description="Detailed prompt metadata configurations and active model mapping."
        icon={<BookOpen className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Prompt details</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <a href="/dashboard/prompts/testing">
              <Button variant="outline" size="sm" className="h-8 text-[11px] border-white/5 bg-neutral-900">
                <Play className="w-3.5 h-3.5 mr-1" />
                Test Prompt
              </Button>
            </a>
            <a href="/dashboard/prompts/editor">
              <Button variant="violet" size="sm" className="h-8 text-[11px]">
                <Edit3 className="w-3.5 h-3.5 mr-1" />
                Edit Prompt
              </Button>
            </a>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* PROMPT CONTENT WORKSPACE (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card className="flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h3 className="font-bold text-white text-sm">Template Instructions Content</h3>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleCopy} 
                className="h-7 text-[10px] border-white/5 bg-neutral-900"
              >
                <Copy className="w-3 h-3 mr-1" />
                Copy instructions
              </Button>
            </div>

            <div className="p-4 rounded-xl bg-black/40 border border-white/5 font-mono text-xs text-neutral-300 leading-relaxed min-h-[160px] whitespace-pre-wrap select-text">
              {prompt.content}
            </div>

            {/* Variable chips */}
            {prompt.variables.length > 0 && (
              <div className="flex flex-col gap-2 mt-1.5">
                <span className="text-[10px] text-neutral-500 font-bold uppercase">Detected placeholder tags:</span>
                <div className="flex flex-wrap gap-1.5">
                  {prompt.variables.map((v: any) => (
                    <span key={v} className="text-[9px] font-mono bg-violet-600/10 border border-violet-500/20 text-violet-300 px-2 py-0.5 rounded">
                      {`{{${v}}}`}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Connected Downstream consumers */}
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Linked Downstream AI Consumers</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Viptant sub-modules consuming this prompt template family as their core behavior instruction.</p>
            </div>

            <div className="flex flex-col gap-3">
              {[
                { name: 'AI Chat Sandbox', route: '/dashboard/ai/chat', status: 'Active' },
                { name: 'CRM Assistant Agent', route: '/dashboard/crm', status: 'Active' },
                { name: 'Content Draft Generator', route: '/dashboard/generator', status: 'Active' },
              ].map((agent) => (
                <div 
                  key={agent.name} 
                  className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs"
                >
                  <span className="font-bold text-white">{agent.name}</span>
                  <Badge variant="emerald" size="sm" dot>{agent.status}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* METADATA SUMMARY (Right 1 column) */}
        <div className="flex flex-col gap-4">
          <Card className="p-4 flex flex-col gap-4 bg-neutral-950/20">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-violet-400" /> Prompt Specifications
            </span>

            <div className="flex flex-col gap-3.5 text-xs">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Active Version:</span>
                <Badge variant="violet" size="sm">v{prompt.version}</Badge>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Category Tag:</span>
                <span className="text-white font-bold capitalize">{prompt.category}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Release Date:</span>
                <span className="text-white font-mono flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-neutral-400" />
                  {new Date(prompt.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Release Author:</span>
                <span className="text-white flex items-center gap-1">
                  <User className="w-3 h-3 text-neutral-400" />
                  system
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
export { Settings, Sliders };
