import * as React from 'react';
import { usePrompts, usePromptTesting, usePromptProviders } from '../hooks';
import { usePromptsStore } from '../store/prompts';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { 
  Sliders, Play, Terminal, ArrowLeft, Cpu, 
  HelpCircle, Variable, Clock, DollarSign, Sparkles, RefreshCw 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

export function TestingPage() {
  const { prompts } = usePrompts();
  const { test, isTesting, testResult } = usePromptTesting();
  const store = usePromptsStore();
  const { providers, models } = usePromptProviders(store.testProvider);

  const [activePromptName, setActivePromptName] = React.useState<string>('');
  const [typedOutput, setTypedOutput] = React.useState('');

  const providerSelectOptions = React.useMemo(() => {
    return providers.map((p: any) => ({
      label: `${p.name.toUpperCase()} AI Gateway`,
      value: p.name.toLowerCase(),
    }));
  }, [providers]);

  const modelSelectOptions = React.useMemo(() => {
    if (models.length > 0) {
      return models.map((m: any) => ({
        label: m.model_name,
        value: m.model_name,
      }));
    }
    // Dynamic fallbacks per provider
    if (store.testProvider === 'groq') {
      return [
        { label: 'llama-3.3-70b-versatile', value: 'llama-3.3-70b-versatile' },
        { label: 'llama-3.1-70b-versatile', value: 'llama-3.1-70b-versatile' },
        { label: 'llama-3.1-8b-instant', value: 'llama-3.1-8b-instant' },
        { label: 'deepseek-r1-distill-llama-70b', value: 'deepseek-r1-distill-llama-70b' },
        { label: 'qwen-qwq-32b', value: 'qwen-qwq-32b' },
      ];
    }
    return [
      { label: 'gpt-4o-mini', value: 'gpt-4o-mini' },
      { label: 'claude-3-5-sonnet-20240620', value: 'claude-3-5-sonnet-20240620' },
      { label: 'gemini-1.5-flash', value: 'gemini-1.5-flash' },
    ];
  }, [models, store.testProvider]);

  // Find the selected prompt template
  const activePrompt = React.useMemo(() => {
    return prompts.find((p: any) => p.name === activePromptName) || null;
  }, [prompts, activePromptName]);

  // Extract variables when selected prompt changes
  React.useEffect(() => {
    if (activePrompt) {
      store.clearTestVariables();
    }
  }, [activePrompt]);

  // Auto-select first prompt on load
  React.useEffect(() => {
    if (prompts.length > 0 && !activePromptName) {
      setActivePromptName(prompts[0].name);
    }
  }, [prompts, activePromptName]);

  // Simulation typing effect on test result load
  React.useEffect(() => {
    if (testResult?.output) {
      setTypedOutput('');
      let index = 0;
      const text = testResult.output;
      const timer = setInterval(() => {
        setTypedOutput((prev) => prev + text.charAt(index));
        index++;
        if (index >= text.length) {
          clearInterval(timer);
        }
      }, 15);
      return () => clearInterval(timer);
    }
  }, [testResult]);

  const handleRun = async () => {
    if (!activePrompt) return;
    
    // Check if variables are supplied
    const missing = activePrompt.variables.filter((v: any) => !store.testVariables[v]);
    if (missing.length > 0) {
      toast.error('Variables missing', `Fill in values for {{${missing.join(', ')}}}`);
      return;
    }

    try {
      await test({
        provider: store.testProvider,
        model: store.testModel,
        content: activePrompt.content,
        variables: store.testVariables,
      });
      toast.success('Simulation Complete', 'Testing completion output generated.');
    } catch (err) {
      toast.error('Testing failed', 'Could not run sandbox completions.');
    }
  };

  const promptOptions = React.useMemo(() => {
    return prompts.map((p: any) => ({ label: p.name, value: p.name }));
  }, [prompts]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors">
        <a href="/dashboard/prompts" className="inline-flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </a>
      </div>

      <PageHeader
        title="Prompt Testing Lab"
        description="Test and debug prompt versions across multiple model gateways and variables datasets."
        icon={<Sliders className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Testing Lab</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* PARAMS & VARIABLES CONFIG (Left 1 column) */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <Card className="flex flex-col gap-4">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-violet-400" /> Gateway Settings
            </span>

            <div className="flex flex-col gap-3 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="text-[9px] text-neutral-400 font-bold uppercase">Select Prompt</label>
                {promptOptions.length > 0 && (
                  <Select
                    value={activePromptName}
                    onChange={(e) => setActivePromptName(e.target.value)}
                    className="bg-neutral-900 border-white/5 h-8 text-[11px]"
                    options={promptOptions}
                  />
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[9px] text-neutral-400 font-bold uppercase">Provider</label>
                <Select
                  value={store.testProvider}
                  onChange={(e) => store.setTestProvider(e.target.value)}
                  className="bg-neutral-900 border-white/5 h-8 text-[11px]"
                  options={providerSelectOptions}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[9px] text-neutral-400 font-bold uppercase">Inference Model</label>
                <Select
                  value={store.testModel}
                  onChange={(e) => store.setTestModel(e.target.value)}
                  className="bg-neutral-900 border-white/5 h-8 text-[11px]"
                  options={modelSelectOptions}
                />
              </div>
            </div>
          </Card>

          {/* Variable Inputs Form */}
          <Card className="flex flex-col gap-4">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Variable className="w-3.5 h-3.5 text-violet-400" /> Variable values
            </span>

            <div className="flex flex-col gap-3.5">
              {activePrompt?.variables.map((v: any) => (
                <div key={v} className="flex flex-col gap-1.5 text-xs">
                  <span className="font-bold text-white font-mono text-[10px]">{`{{${v}}}`}</span>
                  <Input
                    placeholder="Value..."
                    value={store.testVariables[v] || ''}
                    onChange={(e) => store.setTestVariable(v, e.target.value)}
                    className="bg-neutral-950/40 border-white/5 h-8 text-[11px]"
                  />
                </div>
              ))}

              {(!activePrompt || activePrompt.variables.length === 0) && (
                <span className="text-[10px] text-neutral-500 text-center py-6">
                  No variables detected in prompt.
                </span>
              )}
            </div>

            <div className="border-t border-white/5 pt-3.5 mt-2 flex justify-end">
              <Button
                variant="violet"
                size="sm"
                onClick={handleRun}
                disabled={isTesting}
                className="w-full h-8 text-xs font-semibold"
              >
                {isTesting ? (
                  <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 mr-1" />
                )}
                Run Test Completions
              </Button>
            </div>
          </Card>
        </div>

        {/* OUTPUT INSPECTION & TELEMETRY (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card className="flex flex-col gap-4 min-h-[360px]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-violet-400" />
                <div>
                  <h3 className="font-bold text-white text-sm">Sandbox Output Console</h3>
                  <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Rendered completion outputs generated by models.</p>
                </div>
              </div>

              {testResult && (
                <div className="flex items-center gap-2 text-[10px] font-mono">
                  <Badge variant="neutral" className="text-amber-400 border border-amber-500/10 gap-1 font-mono">
                    <Clock className="w-3 h-3" />
                    {testResult.latency_ms}ms
                  </Badge>
                  <Badge variant="neutral" className="text-sky-400 border border-sky-500/10 gap-1 font-mono">
                    <Sparkles className="w-3 h-3" />
                    {testResult.tokens_used} t
                  </Badge>
                  <Badge variant="neutral" className="text-emerald-400 border border-emerald-500/10 gap-1 font-mono">
                    <DollarSign className="w-3 h-3" />
                    ${testResult.cost_usd.toFixed(5)}
                  </Badge>
                </div>
              )}
            </div>

            {/* Output view area */}
            <div className="flex-1 rounded-xl border border-white/5 bg-black/40 p-4 font-mono text-xs text-neutral-300 leading-relaxed min-h-[250px] whitespace-pre-wrap max-h-[400px] overflow-y-auto">
              {isTesting ? (
                <div className="flex flex-col gap-2.5 animate-pulse py-8">
                  <div className="h-4 bg-neutral-900 rounded w-2/3" />
                  <div className="h-4 bg-neutral-900 rounded w-1/2" />
                  <div className="h-4 bg-neutral-900 rounded w-3/4" />
                </div>
              ) : typedOutput ? (
                typedOutput
              ) : (
                <span className="text-neutral-600 select-none">
                  Console idle. Map settings parameters and click "Run Test" to parse output.
                </span>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

