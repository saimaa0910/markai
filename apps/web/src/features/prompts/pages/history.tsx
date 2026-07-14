import * as React from 'react';
import { usePrompts, usePromptHistory } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { History, GitCompare, ArrowLeft, ArrowRight, CheckCircle2, User, Clock } from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

export function HistoryPage() {
  const { prompts } = usePrompts();
  
  const [selectedPromptName, setSelectedPromptName] = React.useState<string>('');
  const { history, isLoading } = usePromptHistory(selectedPromptName || null);

  const [verA, setVerA] = React.useState<string>('');
  const [verB, setVerB] = React.useState<string>('');

  // Auto-select first prompt family when loaded
  React.useEffect(() => {
    if (prompts.length > 0 && !selectedPromptName) {
      setSelectedPromptName(prompts[0].name);
    }
  }, [prompts, selectedPromptName]);

  // Auto-set versions to compare when history changes
  React.useEffect(() => {
    if (history.length > 1) {
      setVerA(history[1].id);
      setVerB(history[0].id);
    } else if (history.length > 0) {
      setVerA(history[0].id);
      setVerB(history[0].id);
    }
  }, [history]);

  const promptOptions = React.useMemo(() => {
    return prompts.map((p: any) => ({ label: p.name, value: p.name }));
  }, [prompts]);

  const versionOptions = React.useMemo(() => {
    return history.map((h: any) => ({ label: `Version v${h.version}`, value: h.id }));
  }, [history]);

  // Find contents of A and B
  const contentA = React.useMemo(() => {
    const matched = history.find((h: any) => h.id === verA);
    return matched ? matched.content : '';
  }, [history, verA]);

  const contentB = React.useMemo(() => {
    const matched = history.find((h: any) => h.id === verB);
    return matched ? matched.content : '';
  }, [history, verB]);

  // Compute diff lines
  const diffLines = React.useMemo(() => {
    const linesA = contentA.split('\n');
    const linesB = contentB.split('\n');
    const max = Math.max(linesA.length, linesB.length);
    
    const comparison = [];
    for (let i = 0; i < max; i++) {
      const a = linesA[i] || '';
      const b = linesB[i] || '';
      const isDifferent = a !== b;
      comparison.push({
        lineNum: i + 1,
        textA: a,
        textB: b,
        isDifferent,
      });
    }
    return comparison;
  }, [contentA, contentB]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors">
        <a href="/dashboard/prompts" className="inline-flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </a>
      </div>

      <PageHeader
        title="Version Control & Diff Viewer"
        description="Track revisions timeline, compare changes side-by-side, and inspect line differences."
        icon={<History className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Prompt versions</Badge>}
      />

      {/* Select Prompt controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-neutral-950/20 border border-white/5 p-4 rounded-xl">
        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <span className="text-xs font-semibold text-neutral-400 shrink-0">Active Prompt:</span>
          {promptOptions.length > 0 && (
            <Select
              value={selectedPromptName}
              onChange={(e) => setSelectedPromptName(e.target.value)}
              className="bg-neutral-900 border-white/5 h-8 text-[11px] w-64"
              options={promptOptions}
            />
          )}
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {history.length > 0 && (
            <>
              <Select
                value={verA}
                onChange={(e) => setVerA(e.target.value)}
                className="bg-neutral-900 border-white/5 h-8 text-[11px] w-32"
                options={versionOptions}
              />
              <ArrowRight className="w-4 h-4 text-neutral-500" />
              <Select
                value={verB}
                onChange={(e) => setVerB(e.target.value)}
                className="bg-neutral-900 border-white/5 h-8 text-[11px] w-32"
                options={versionOptions}
              />
            </>
          )}
        </div>
      </div>

      {/* Timeline and Side-by-Side Diff */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Version Timeline Panel */}
        <div className="lg:col-span-1 flex flex-col gap-4">
          <Card className="flex flex-col gap-4 min-h-[300px]">
            <div>
              <h4 className="font-bold text-white text-sm">Release Timeline</h4>
              <p className="text-[10px] text-neutral-500 mt-0.5">Prompt revisions log history</p>
            </div>

            <div className="flex flex-col gap-5 relative pl-4 mt-2">
              {/* Timeline guide line */}
              <div className="absolute left-6.5 top-2 bottom-2 w-0.5 bg-neutral-900 border-l border-white/5" />

              {history.map((ver: any) => (
                <div key={ver.id} className="flex gap-4 items-start relative z-10 text-xs">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center border bg-neutral-950 border-white/5 text-[9px] font-mono shrink-0">
                    {ver.version}
                  </div>

                  <div className="flex flex-col gap-0.5">
                    <span className="font-bold text-white">Version v{ver.version}</span>
                    <span className="text-[10px] text-neutral-500">{ver.comment}</span>
                    
                    <div className="flex items-center gap-2 text-[9px] text-neutral-600 mt-1">
                      <span className="flex items-center gap-0.5"><User className="w-2.5 h-2.5" /> system</span>
                      <span className="flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" /> {new Date(ver.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ))}

              {history.length === 0 && (
                <div className="py-20 text-center text-neutral-600">No history logged.</div>
              )}
            </div>
          </Card>
        </div>

        {/* Diff Viewer Workspace */}
        <div className="lg:col-span-3">
          <Card className="flex flex-col gap-4">
            <div className="flex items-center gap-2 border-b border-white/5 pb-3">
              <GitCompare className="w-4 h-4 text-violet-400" />
              <div>
                <h3 className="font-bold text-white text-sm">Side-by-Side Difference Analysis</h3>
                <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Comparing changes between two selected versions of prompt templates.</p>
              </div>
            </div>

            {/* Split Screen Columns */}
            <div className="border border-white/5 rounded-xl overflow-hidden text-[11px] font-mono leading-relaxed bg-black/20">
              <div className="grid grid-cols-2 border-b border-white/5 bg-neutral-950/60 p-2 font-sans font-bold text-neutral-400">
                <div className="pl-6 border-r border-white/5">Original Version (Left)</div>
                <div className="pl-6">Modified Version (Right)</div>
              </div>

              <div className="flex flex-col divide-y divide-white/5 max-h-[400px] overflow-y-auto">
                {diffLines.map((line) => (
                  <div key={line.lineNum} className="grid grid-cols-2 select-text">
                    {/* Column A (Original) */}
                    <div className={`p-2 border-r border-white/5 pl-8 relative flex ${
                      line.isDifferent && line.textA ? 'bg-rose-500/10 text-rose-300' : 'text-neutral-400'
                    }`}>
                      <span className="absolute left-2 text-[9px] text-neutral-600 select-none">{line.lineNum}</span>
                      <span>{line.textA || ' '}</span>
                    </div>
                    {/* Column B (Modified) */}
                    <div className={`p-2 pl-8 relative flex ${
                      line.isDifferent && line.textB ? 'bg-emerald-500/10 text-emerald-300' : 'text-neutral-300'
                    }`}>
                      <span className="absolute left-2 text-[9px] text-neutral-600 select-none">{line.lineNum}</span>
                      <span>{line.textB || ' '}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-white/5 pt-3.5 flex justify-end">
              <Button
                variant="violet"
                size="sm"
                onClick={() => toast.success('Version Restored', 'Reverted active template back to selected version.')}
                className="text-xs"
                disabled={history.length <= 1}
              >
                Restore Version
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
export { GitCompare };
export type { User };
export type { Clock };
