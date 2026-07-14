import * as React from 'react';
import { useModels, useProviders } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Textarea, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { 
  Terminal, Sparkles, RefreshCw, Play, Square, Download, 
  Copy, Save, FileText, Code, Table, Eye, Settings2, Sliders, Info, Activity 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';

interface PromptTemplate {
  name: string;
  systemPrompt: string;
  userPrompt: string;
  variables: Record<string, string>;
  sampleResponse: string;
}

const TEMPLATES: PromptTemplate[] = [
  {
    name: 'Draft Marketing Email',
    systemPrompt: 'You are an expert enterprise copywriter. Draft engaging, professional campaign variants.',
    userPrompt: 'Create a product launch email for {{product_name}} focusing on its core value: {{core_benefit}}. Use a {{tone}} tone of voice.',
    variables: { product_name: 'Viptant OS', core_benefit: 'Autonomous AI Agent workflows', tone: 'professional' },
    sampleResponse: `Subject: Introducing Viptant OS – Unleash the Power of Autonomous AI Workflows

Dear Marketing Leader,

In today's fast-paced enterprise landscape, scaling your digital campaigns efficiently is no longer just an advantage—it is a necessity. 

We are thrilled to introduce Viptant OS, the next generation Enterprise AI Marketing Operating System. Built specifically for modern workspaces, Viptant OS empowers your teams to deploy autonomous AI agent workflows that handle everything from provider health monitoring to dynamic copy variant generations in real time.

Why Viptant OS is a game-changer:
1. **Multi-Model Orchestrations**: Dynamic routing models select the absolute cheapest, lowest latency providers for every chat context automatically.
2. **Resilience Fallbacks**: Rest assured knowing failing connection checks trigger standbys immediately, keeping pipelines active.
3. **Data Telemetry Analytics**: View live cost breakdowns, token heatmaps, and hourly peak loads on an intuitive premium console dashboard.

Are you ready to scale your campaign operations effortlessly?

Best regards,
The Viptant Architect Team`,
  },
  {
    name: 'React UI Code Generator',
    systemPrompt: 'You are a Senior React Engineer. Generate clean, modular components with Tailwind CSS.',
    userPrompt: 'Create a responsive component for a {{component_name}} featuring a {{styling_style}} design theme.',
    variables: { component_name: 'Statistic card grid', styling_style: 'glassmorphism dark mode' },
    sampleResponse: `\`\`\`tsx
import * as React from 'react';
import { motion } from 'framer-motion';
import { ArrowUpRight, Cpu, Activity } from 'lucide-react';

export function StatGrid() {
  const stats = [
    { title: 'API Inferences', value: '45.2k', change: '+12.4%', label: 'Active streams' },
    { title: 'Gateway Latency', value: '180ms', change: '-4.2%', label: 'LPU roundtrip' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-6 bg-black/40 backdrop-blur-md border border-white/10 rounded-2xl">
      {stats.map((stat, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="p-5 rounded-xl border border-white/5 bg-neutral-950/40 hover:border-violet-500/20 transition-all flex flex-col gap-3 group"
        >
          <div className="flex justify-between items-start">
            <span className="text-xs text-neutral-400 font-medium">{stat.title}</span>
            <ArrowUpRight className="w-4 h-4 text-violet-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white font-mono">{stat.value}</span>
            <span className="text-xs font-semibold text-emerald-400">{stat.change}</span>
          </div>
          <span className="text-[10px] text-neutral-500 font-medium">{stat.label}</span>
        </motion.div>
      ))}
    </div>
  );
}
\`\`\``,
  },
];

export function PlaygroundPage() {
  const { models } = useModels();
  const { providers } = useProviders();

  // Selected Provider & Model keys
  const [selProv, setSelProv] = React.useState('openai');
  const [selModel, setSelModel] = React.useState('');

  // Settings
  const [temperature, setTemperature] = React.useState(0.7);
  const [topP, setTopP] = React.useState(0.9);
  const [maxTokens, setMaxTokens] = React.useState(2048);
  const [jsonMode, setJsonMode] = React.useState(false);
  const [systemPrompt, setSystemPrompt] = React.useState('You are a helpful AI coding assistant.');
  const [userPrompt, setUserPrompt] = React.useState('Draft a response variable greeting to {{user_name}}.');
  const [variables, setVariables] = React.useState<Record<string, string>>({ user_name: 'Architect' });

  // Output response states
  const [responseOutput, setResponseOutput] = React.useState('');
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [outputView, setOutputView] = React.useState<'markdown' | 'code' | 'raw' | 'streaming'>('markdown');
  
  // Streaming controller reference
  const timerRef = React.useRef<NodeJS.Timeout | null>(null);

  // Set default model on load
  React.useEffect(() => {
    const provModels = models.filter((m) => m.provider === selProv);
    if (provModels.length > 0) {
      setSelModel(provModels[0].model_name);
    }
  }, [selProv, models]);

  // Parse prompt variables when userPrompt changes
  React.useEffect(() => {
    const variableRegex = /\{\{([^}]+)\}\}/g;
    let match;
    const detected: Record<string, string> = {};
    while ((match = variableRegex.exec(userPrompt)) !== null) {
      const varName = match[1].trim();
      detected[varName] = variables[varName] || '';
    }
    setVariables(detected);
  }, [userPrompt]);

  const handleTemplateLoad = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = Number(e.target.value);
    if (isNaN(idx)) return;
    const temp = TEMPLATES[idx];
    setSystemPrompt(temp.systemPrompt);
    setUserPrompt(temp.userPrompt);
    setVariables(temp.variables);
    toast.success('Template Loaded', `${temp.name} is now loaded in prompt panels.`);
  };

  const handleVariableChange = (key: string, val: string) => {
    setVariables((prev) => ({ ...prev, [key]: val }));
  };

  const handleGenerate = async () => {
    if (isGenerating) return;

    // Render variables
    let compiledPrompt = userPrompt;
    Object.entries(variables).forEach(([key, val]) => {
      compiledPrompt = compiledPrompt.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), val || `{{${key}}}`);
    });

    setIsGenerating(true);
    setResponseOutput('');

    // Determine target template answer or default
    const matchingTemplate = TEMPLATES.find((t) => t.userPrompt.slice(0, 15) === userPrompt.slice(0, 15));
    const targetResponse = matchingTemplate 
      ? matchingTemplate.sampleResponse 
      : `Response generated using ${selModel || 'model'} preset:\n\nUser Prompt: "${compiledPrompt}"\n\nTemperature config: ${temperature}\nSystem Instructions: "${systemPrompt}"\n\nTask compiled successfully.`;

    let currentIdx = 0;
    timerRef.current = setInterval(() => {
      if (currentIdx < targetResponse.length) {
        setResponseOutput((prev) => prev + targetResponse.charAt(currentIdx));
        currentIdx += 2;
      } else {
        if (timerRef.current) clearInterval(timerRef.current);
        setIsGenerating(false);
        toast.success('Generation Complete', 'Response output generated.');
      }
    }, 10);
  };

  const handleStop = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      setIsGenerating(false);
      toast.info('Generation Stopped', 'Output generation suspended.');
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(responseOutput);
    toast.success('Copied', 'Output response copied to clipboard.');
  };

  const handleDownload = () => {
    const blob = new Blob([responseOutput], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `playground_response_${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Downloaded', 'Response output file downloaded.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="AI Playground"
        description="Write and test prompts, adjust settings dynamically, and view responses formatted as markdown or raw code."
        icon={<Terminal className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Prompt Lab</Badge>}
      />

      {/* Main Sandbox Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: PARAMETERS & INPUTS */}
        <div className="flex flex-col gap-5 lg:col-span-1">
          {/* Templates loader card */}
          <Card className="p-4 flex flex-col gap-3">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Templates Library</span>
            <Select 
              onChange={handleTemplateLoad} 
              className="bg-neutral-900 border-white/5 h-9 text-xs"
              options={[
                { label: 'Select prompt template...', value: 'none' },
                ...TEMPLATES.map((t, idx) => ({ label: t.name, value: String(idx) }))
              ]}
            />
          </Card>

          {/* Prompt inputs card */}
          <Card className="flex flex-col gap-4">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Prompt Editor</span>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">System Instructions</label>
              <Textarea 
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="bg-neutral-950/40 border-white/5 text-xs h-20 placeholder-neutral-600 resize-none"
                placeholder="E.g. You are a code generator assistant..."
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">User Prompt (Use double braces for {"{{variables}}"})</label>
              <Textarea 
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                className="bg-neutral-950/40 border-white/5 text-xs h-32 placeholder-neutral-600 resize-none font-mono"
                placeholder="E.g. Hello {{name}}!"
              />
            </div>

            {/* Variable slots inputs */}
            {Object.keys(variables).length > 0 && (
              <div className="flex flex-col gap-3 border-t border-white/5 pt-4">
                <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-violet-400" />
                  Prompt Variables Detect
                </span>
                <div className="flex flex-col gap-2">
                  {Object.entries(variables).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-2">
                      <span className="text-[10px] text-neutral-500 font-mono w-24 truncate">{key}</span>
                      <Input
                        value={val}
                        onChange={(e) => handleVariableChange(key, e.target.value)}
                        placeholder={`Value for ${key}`}
                        className="bg-neutral-950/40 border-white/5 h-8 text-[11px]"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Hyperparameters card */}
          <Card className="flex flex-col gap-4">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
              <Settings2 className="w-3.5 h-3.5 text-neutral-600" /> Hyperparameters
            </span>

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-neutral-400 font-semibold">Temperature: {temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full accent-violet-600"
              />
            </div>

            <div className="flex flex-col gap-2 mt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-neutral-400 font-semibold">Top P: {topP}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(Number(e.target.value))}
                className="w-full accent-violet-600"
              />
            </div>

            <div className="flex flex-col gap-1.5 mt-2">
              <label className="text-xs text-neutral-400 font-semibold">Max Completion Length</label>
              <Input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
                className="bg-neutral-950/40 border-white/5 h-9 text-xs"
              />
            </div>
          </Card>
        </div>

        {/* RIGHT PANEL: SELECTORS, CONTROL ROW, OUTPUT SCREEN */}
        <div className="lg:col-span-2 flex flex-col gap-5">
          {/* Preset Selectors row */}
          <Card className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center flex-wrap gap-3 flex-1">
              <div className="min-w-[140px]">
                <Select
                  value={selProv}
                  onChange={(e) => setSelProv(e.target.value)}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={providers.map((p) => ({ label: p.name, value: p.key }))}
                />
              </div>

              <div className="min-w-[180px]">
                <Select
                  value={selModel}
                  onChange={(e) => setSelModel(e.target.value)}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={models
                    .filter((m) => m.provider === selProv)
                    .map((m) => ({ label: `${m.name} (${m.model_name})`, value: m.model_name }))}
                />
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {isGenerating ? (
                <Button variant="outline" size="sm" onClick={handleStop} className="h-9 text-[11px] text-rose-400 border-rose-500/10">
                  <Square className="w-3.5 h-3.5 mr-1 text-rose-400 fill-rose-500/20" />
                  Stop Output
                </Button>
              ) : (
                <Button variant="violet" size="sm" onClick={handleGenerate} className="h-9 text-[11px]">
                  <Play className="w-3.5 h-3.5 mr-1" />
                  Run Inferences
                </Button>
              )}
            </div>
          </Card>

          {/* Response output terminal card */}
          <Card className="flex-1 flex flex-col gap-4 min-h-[450px]">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-1.5 text-xs text-neutral-400 font-bold uppercase tracking-wider">
                <Terminal className="w-4 h-4 text-violet-400" />
                Response terminal screen
              </div>

              {/* View options */}
              <div className="flex items-center gap-2">
                <div className="flex items-center rounded-lg bg-neutral-900 border border-white/5 p-0.5 text-[10px]">
                  {[
                    { id: 'markdown', label: 'Preview', icon: <Eye className="w-3 h-3" /> },
                    { id: 'code', label: 'Code', icon: <Code className="w-3 h-3" /> },
                    { id: 'raw', label: 'Raw Text', icon: <FileText className="w-3 h-3" /> },
                    { id: 'streaming', label: 'Inspector', icon: <Activity className="w-3 h-3" /> },
                  ].map((btn) => (
                    <button
                      key={btn.id}
                      onClick={() => setOutputView(btn.id as any)}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded transition-all cursor-pointer ${
                        outputView === btn.id ? 'bg-violet-600 text-white shadow' : 'text-neutral-400 hover:text-white'
                      }`}
                    >
                      {btn.icon}
                      <span>{btn.label}</span>
                    </button>
                  ))}
                </div>

                <div className="w-px h-4 bg-white/5" />

                <button 
                  onClick={handleCopy} 
                  disabled={!responseOutput}
                  className="p-1.5 rounded-lg border border-white/5 hover:bg-neutral-900 text-neutral-400 hover:text-white transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
                <button 
                  onClick={handleDownload} 
                  disabled={!responseOutput}
                  className="p-1.5 rounded-lg border border-white/5 hover:bg-neutral-900 text-neutral-400 hover:text-white transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Output view window */}
            <div className="flex-1 p-4 rounded-xl bg-black/40 border border-white/5 font-mono text-xs overflow-y-auto text-neutral-200 leading-relaxed max-h-[400px]">
              {responseOutput || outputView === 'streaming' ? (
                outputView === 'markdown' ? (
                  // Simple high-fidelity render helper for Markdown preview
                  <div className="flex flex-col gap-3 font-sans text-neutral-300">
                    {responseOutput.split('\n\n').map((para, i) => {
                      if (para.startsWith('###')) {
                        return <h4 key={i} className="text-white font-bold text-sm mt-2">{para.replace('###', '').trim()}</h4>;
                      }
                      if (para.startsWith('-')) {
                        return (
                          <ul key={i} className="list-disc pl-5 flex flex-col gap-1">
                            {para.split('\n').map((li, j) => (
                              <li key={j}>{li.replace('-', '').trim()}</li>
                            ))}
                          </ul>
                        );
                      }
                      return <p key={i}>{para}</p>;
                    })}
                  </div>
                ) : outputView === 'code' ? (
                  <pre className="whitespace-pre-wrap">{responseOutput}</pre>
                ) : outputView === 'raw' ? (
                  <pre className="whitespace-pre-wrap">{responseOutput}</pre>
                ) : (
                  // Streaming Inspector Panel
                  <div className="flex flex-col gap-5 font-sans text-neutral-300">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg bg-neutral-900 border border-white/5 flex flex-col gap-1">
                        <span className="text-[9px] text-neutral-500 uppercase font-semibold">Streaming Speed</span>
                        <span className="text-sm font-bold font-mono text-violet-400">
                          {isGenerating ? '65 tokens/sec' : '0 tokens/sec'}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-neutral-900 border border-white/5 flex flex-col gap-1">
                        <span className="text-[9px] text-neutral-500 uppercase font-semibold">Connection Status</span>
                        <span className="text-sm font-bold font-mono text-emerald-400">
                          {isGenerating ? 'ACTIVE STREAMING' : 'STANDBY'}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (isGenerating) {
                            handleStop();
                            toast.info('Streaming Paused', 'Completion generation paused.');
                          } else {
                            handleGenerate();
                            toast.success('Streaming Resumed', 'Resuming completion pipeline.');
                          }
                        }}
                        className="h-8 text-[10px] border-white/5 text-neutral-300 hover:text-white"
                      >
                        {isGenerating ? 'Pause Stream' : 'Resume Stream'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          handleStop();
                          toast.success('Connection Reset', 'Reconnected socket pipeline.');
                        }}
                        className="h-8 text-[10px] border-white/5 text-neutral-300 hover:text-white"
                      >
                        Reconnect Socket
                      </Button>
                    </div>

                    <div className="flex flex-col gap-1.5 border-t border-white/5 pt-3">
                      <span className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Streaming Telemetry Log</span>
                      <pre className="p-3 rounded bg-neutral-950 text-[11px] font-mono text-neutral-400 border border-white/5 max-h-[150px] overflow-y-auto whitespace-pre-wrap">
                        {responseOutput || 'No streaming events logged.'}
                      </pre>
                    </div>
                  </div>
                )
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center gap-2 py-20 text-neutral-600 font-sans">
                  <Terminal className="w-8 h-8" />
                  <span className="text-xs font-semibold">Terminal Standing By</span>
                  <span className="text-[10px] mt-0.5">Click Run Inferences to execute compile scripts and generate output response logs.</span>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
