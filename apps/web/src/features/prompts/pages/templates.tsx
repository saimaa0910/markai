import * as React from 'react';
import { usePromptTemplates, usePrompts } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { Library, Star, Plus, Copy, CheckCircle2 } from 'lucide-react';
import { toast } from '@/components/ui/toast';

export function TemplatesPage() {
  const { templates } = usePromptTemplates();
  const { createPrompt } = usePrompts();

  const handleImport = (template: any) => {
    createPrompt.mutate({
      name: template.name.toLowerCase().replace(/\s+/g, '_'),
      content: template.content,
      category: template.category,
      tags: template.tags,
      is_shared: true,
      version: 1,
    }, {
      onSuccess: () => {
        toast.success('Template Imported', `Imported ${template.name} into prompt registry.`);
      },
      onError: () => {
        toast.error('Import Failed', 'Could not save template.');
      }
    });
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Prompt Template Gallery"
        description="Select and clone from predesigned crm flow, marketing copy, and email template prompts."
        icon={<Library className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Prompt gallery</Badge>}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((tpl: any) => (
          <Card 
            key={tpl.name}
            className="flex flex-col gap-4 border border-white/5 hover:border-violet-500/20 transition-all p-5 bg-neutral-950/10 group relative"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex flex-col">
                <span className="text-xs font-bold text-white group-hover:text-violet-400 transition-colors">
                  {tpl.name}
                </span>
                <span className="text-[10px] text-neutral-500 font-mono mt-0.5">
                  Category: {tpl.category}
                </span>
              </div>
              <Badge variant="violet" className="text-[8px] font-bold uppercase">Ready</Badge>
            </div>

            <p className="text-[11px] text-neutral-400 font-mono line-clamp-3 min-h-[48px] leading-relaxed">
              {tpl.content}
            </p>

            <div className="flex items-center gap-1.5 flex-wrap">
              {tpl.tags.map((tag: any) => (
                <span key={tag} className="text-[9px] font-mono bg-neutral-900 border border-white/5 rounded px-1.5 py-0.5 text-neutral-500">
                  {tag}
                </span>
              ))}
            </div>

            <div className="border-t border-white/5 pt-3.5 mt-2 flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(tpl.content);
                  toast.success('Copied to Clipboard');
                }}
                className="h-7 text-[10px] border-white/5 bg-neutral-900"
              >
                <Copy className="w-3 h-3 mr-1" />
                Copy Content
              </Button>
              <Button
                variant="violet"
                size="sm"
                onClick={() => handleImport(tpl)}
                className="h-7 text-[10px]"
              >
                <Plus className="w-3 h-3 mr-1" />
                Clone template
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
export { Star, Plus, Copy, CheckCircle2 };
export type { Library };
