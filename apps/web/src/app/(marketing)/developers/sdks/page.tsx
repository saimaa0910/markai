'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, ShieldCheck, Cpu, ArrowRight, Github, ExternalLink, Sparkles, ChevronRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { CodeBlock } from '@/components/ui/code-block';
import { useRouter } from 'next/navigation';

interface SDK {
  id: string;
  lang: string;
  pkg: string;
  install: string;
  code: string;
  gh: string;
  badge: string;
  color: string;
}

const SDKS: SDK[] = [
  {
    id: 'node',
    lang: 'Node.js',
    pkg: '@viptant/node v1.2.4',
    install: 'npm install @viptant/node',
    gh: 'https://github.com/viptant/viptant-node',
    badge: 'NPM REGISTRY',
    color: 'from-emerald-500/10 to-teal-500/10 border-emerald-500/20 text-emerald-400',
    code: `const { ViptantClient } = require('@viptant/node');\n\nconst viptant = new ViptantClient({\n  apiKey: process.env.VIPTANT_API_KEY\n});\n\n// Create a content agent\nconst agent = await viptant.agents.create({\n  name: 'copywriter-1',\n  role: 'content',\n  instructions: 'Draft brand-aligned email outlines'\n});\n\nconsole.log(\`Agent Created: \${agent.id}\`);`,
  },
  {
    id: 'python',
    lang: 'Python',
    pkg: 'viptant-python v1.2.0',
    install: 'pip install viptant',
    gh: 'https://github.com/viptant/viptant-python',
    badge: 'PYPI REGISTRY',
    color: 'from-blue-500/10 to-indigo-500/10 border-blue-500/20 text-blue-400',
    code: `from viptant import ViptantClient\nimport os\n\nclient = ViptantClient(\n    api_key=os.environ.get("VIPTANT_API_KEY")\n)\n\n# Create a content agent\nagent = client.agents.create(\n    name="copywriter-1",\n    role="content",\n    instructions="Draft brand-aligned email outlines"\n)\n\nprint(f"Agent Created: {agent.id}")`,
  },
  {
    id: 'go',
    lang: 'Go',
    pkg: 'github.com/viptant/viptant-go v0.9.1',
    install: 'go get github.com/viptant/viptant-go',
    gh: 'https://github.com/viptant/viptant-go',
    badge: 'GO MODULES',
    color: 'from-cyan-500/10 to-blue-500/10 border-cyan-500/20 text-cyan-400',
    code: `package main\n\nimport (\n\t"context"\n\t"fmt"\n\t"os"\n\t"github.com/viptant/viptant-go"\n)\n\nfunc main() {\n\tclient := viptant.NewClient(os.Getenv("VIPTANT_API_KEY"))\n\t\n\tagent, _ := client.Agents.Create(context.Background(), viptant.AgentParams{\n\t\tName: "copywriter-1",\n\t\tRole: "content",\n\t\tInstructions: "Draft brand-aligned email outlines",\n\t})\n\t\n\tfmt.Printf("Agent Created: %s\\n", agent.ID)\n}`,
  },
  {
    id: 'rust',
    lang: 'Rust',
    pkg: 'viptant-rust v0.2.0',
    install: 'cargo add viptant',
    gh: 'https://github.com/viptant/viptant-rust',
    badge: 'CRATES.IO',
    color: 'from-amber-500/10 to-orange-500/10 border-amber-500/20 text-amber-400',
    code: `use viptant::{ViptantClient, AgentParams};\nuse std::env;\n\n#[tokio::main]\nasync fn main() -> Result<(), Box<dyn std::error::Error>> {\n    let api_key = env::var("VIPTANT_API_KEY")?;\n    let client = ViptantClient::new(&api_key)?;\n\n    let agent = client.agents().create(AgentParams {\n        name: "copywriter-1".to_string(),\n        role: "content".to_string(),\n        instructions: "Draft brand-aligned email outlines".to_string(),\n    }).await?;\n\n    println!("Agent Created: {}", agent.id);\n    Ok(())\n}`,
  },
];

export default function SdksPage() {
  const router = useRouter();
  const [selectedSDK, setSelectedSDK] = React.useState<SDK>(SDKS[0]);

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Libraries & Packages</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Officially Supported SDKs
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Accelerate integrations using our native SDK client libraries. Set up keys, configure routes, and interact with agents in your language of choice.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Grid List of Languages ──────────────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {SDKS.map((sdk, idx) => (
            <FadeUp 
              key={sdk.id} 
              delay={idx * 0.05}
            >
              <div
                className={`p-6 rounded-xl border bg-neutral-950/40 cursor-pointer transition-all duration-300 hover:scale-[1.02] flex flex-col justify-between h-full text-left ${
                  selectedSDK.id === sdk.id 
                    ? 'border-violet-500 shadow-lg shadow-violet-600/5' 
                    : 'border-white/6 hover:border-white/10'
                }`}
                onClick={() => setSelectedSDK(sdk)}
              >
                <div>
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded border inline-block mb-4 bg-gradient-to-tr ${sdk.color}`}>
                    {sdk.badge}
                  </span>
                  <h4 className="text-lg font-bold text-white mb-1.5">{sdk.lang}</h4>
                  <p className="text-xs text-neutral-500 font-mono">{sdk.pkg}</p>
                </div>

                <div className="flex items-center justify-between border-t border-white/5 pt-4 mt-6">
                  <a 
                    href={sdk.gh} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-neutral-400 hover:text-white transition-colors p-1"
                    onClick={(e) => e.stopPropagation()} // Stop bubble selecting sdk
                  >
                    <Github className="w-4 h-4" />
                  </a>
                  <span className="text-[10px] font-semibold text-neutral-400 flex items-center gap-1 group">
                    Select Guide <ChevronRight className="w-3.5 h-3.5 text-violet-400" />
                  </span>
                </div>
              </div>
            </FadeUp>
          ))}
        </div>

        {/* Dynamic SDK Guide Block */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start text-left max-w-5xl mx-auto">
          {/* Instructions Column (col-span-5) */}
          <div className="lg:col-span-5 space-y-6">
            <FadeUp>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                Quickstart for {selectedSDK.lang} <Sparkles className="w-4 h-4 text-violet-400" />
              </h3>
              <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed">
                Add the Viptant package dependency to your workspace build, authenticate via system environment tokens, and construct client calls.
              </p>
            </FadeUp>

            <FadeUp delay={0.1} className="space-y-4">
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">1. Installation</span>
                <CodeBlock code={selectedSDK.install} language="bash" copyable />
              </div>

              <div className="space-y-1.5">
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">2. Environment Token</span>
                <CodeBlock code='export VIPTANT_API_KEY="sk_live_..."' language="bash" copyable />
              </div>
            </FadeUp>
          </div>

          {/* Code Reference Preview Column (col-span-7) */}
          <div className="lg:col-span-7 space-y-2">
            <FadeUp delay={0.2}>
              <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block mb-2">3. Initialization Template</span>
              <CodeBlock 
                code={selectedSDK.code} 
                language={selectedSDK.id === 'rust' ? 'rust' : selectedSDK.id === 'go' ? 'go' : selectedSDK.id === 'python' ? 'python' : 'javascript'} 
                copyable 
                maxHeight="320px"
              />
            </FadeUp>
          </div>
        </div>
      </section>

      {/* ─── Bottom CTA banner ──────────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50 text-center relative overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-violet-600/5 blur-[120px] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <FadeUp>
            <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-4">
              Looking for Community Wrappers?
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              Explore open-source, community-maintained wrappers for PHP, C#, Ruby, and Flutter integrations.
            </p>
            <div className="flex justify-center gap-3">
              <Button 
                variant="violet" 
                size="lg"
                onClick={() => router.push('/developers/api-docs')}
                className="h-11 px-6 text-xs font-semibold"
              >
                Read REST Spec <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </div>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}
