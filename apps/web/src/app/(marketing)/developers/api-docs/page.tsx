'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Key, Shield, AlertTriangle, Cpu, Play, 
  Terminal, Sparkles, Check, CheckCircle2, ChevronRight, ArrowRight 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { CodeBlock } from '@/components/ui/code-block';

interface Endpoint {
  method: 'GET' | 'POST';
  path: string;
  name: string;
  desc: string;
  params: { name: string; type: string; req: boolean; desc: string }[];
  curlCode: string;
  nodeCode: string;
  response: string;
}

const ENDPOINTS: Endpoint[] = [
  {
    method: 'POST',
    path: '/v1/agents',
    name: 'Create Agent',
    desc: 'Deploy a new autonomous AI agent with dynamic task instructions and isolated vector memory.',
    params: [
      { name: 'name', type: 'string', req: true, desc: 'Unique identifier name for the agent.' },
      { name: 'role', type: 'string', req: true, desc: 'Specialized role classification (content, crm, campaigns, seo).' },
      { name: 'instructions', type: 'string', req: true, desc: 'Goal statement and execution guidelines for the agent.' },
      { name: 'model_preference', type: 'string', req: false, desc: 'Optional route restriction (gemini, claude, gpt).' },
    ],
    curlCode: `curl -X POST https://api.viptant.com/v1/agents \\\n  -H "Authorization: Bearer YOUR_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d '{\n    "name": "copywriter-agent-1",\n    "role": "content",\n    "instructions": "Draft brand-aligned email copies for cohort users",\n    "model_preference": "gemini"\n  }'`,
    nodeCode: `const axios = require('axios');\n\naxios.post('https://api.viptant.com/v1/agents', {\n  name: 'copywriter-agent-1',\n  role: 'content',\n  instructions: 'Draft brand-aligned email copies for cohort users',\n  model_preference: 'gemini'\n}, {\n  headers: {\n    'Authorization': 'Bearer YOUR_API_KEY'\n  }\n}).then(res => console.log(res.data));`,
    response: `{\n  "id": "agent_8f2e91a0",\n  "name": "copywriter-agent-1",\n  "role": "content",\n  "status": "ready",\n  "created_at": "2026-07-14T21:38:30Z",\n  "version": "1.0.0"\n}`,
  },
  {
    method: 'GET',
    path: '/v1/agents',
    name: 'List Agents',
    desc: 'Retrieve a paginated list of all active AI agents running in your organization.',
    params: [
      { name: 'limit', type: 'integer', req: false, desc: 'Number of records to return. Default: 10.' },
      { name: 'starting_after', type: 'string', req: false, desc: 'Cursor token for pagination.' },
    ],
    curlCode: `curl -X GET https://api.viptant.com/v1/agents?limit=2 \\\n  -H "Authorization: Bearer YOUR_API_KEY"`,
    nodeCode: `const axios = require('axios');\n\naxios.get('https://api.viptant.com/v1/agents?limit=2', {\n  headers: {\n    'Authorization': 'Bearer YOUR_API_KEY'\n  }\n}).then(res => console.log(res.data));`,
    response: `{\n  "object": "list",\n  "data": [\n    {\n      "id": "agent_8f2e91a0",\n      "name": "copywriter-agent-1",\n      "role": "content",\n      "status": "ready"\n    },\n    {\n      "id": "agent_ff38ac91",\n      "name": "crm-enricher-2",\n      "role": "crm",\n      "status": "idle"\n    }\n  ],\n  "has_more": false\n}`,
  },
];

export default function ApiDocsPage() {
  const [activeTab, setActiveTab] = React.useState<'curl' | 'node'>('curl');
  const [selectedEndpoint, setSelectedEndpoint] = React.useState<Endpoint>(ENDPOINTS[0]);
  const [apiKey, setApiKey] = React.useState('');
  const [playgroundResponse, setPlaygroundResponse] = React.useState('Click "Send Request" to test api endpoint...');
  const [playgroundLoading, setPlaygroundLoading] = React.useState(false);

  const handleSendRequest = () => {
    setPlaygroundLoading(true);
    setPlaygroundResponse('Connecting to sandbox gate...');
    
    setTimeout(() => {
      setPlaygroundLoading(false);
      if (!apiKey.trim()) {
        setPlaygroundResponse(`{\n  "error": {\n    "code": "unauthorized",\n    "message": "Missing API token. Authenticate via Bearer authorization headers."\n  }\n}`);
      } else {
        setPlaygroundResponse(selectedEndpoint.response);
      }
    }, 1000);
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Header Hero ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-12 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Developer Hub</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Viptant REST API Reference
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Integrate agentic pipelines, trigger custom campaigns, and enrich lead databases natively using our HTTP endpoints.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Main 3-Column Workspace ────────────────────────────────────── */}
      <section className="max-w-8xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Column 1: Navigation Sidebar (col-span-2) */}
        <div className="lg:col-span-2 hidden lg:block text-left border-r border-white/5 pr-4">
          <div className="space-y-6 sticky top-28">
            <div>
              <h4 className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-3">Getting Started</h4>
              <ul className="space-y-2 text-xs">
                <li><a href="#authentication" className="text-neutral-400 hover:text-white transition-colors">Authentication</a></li>
                <li><a href="#rate-limits" className="text-neutral-400 hover:text-white transition-colors">Rate Limits</a></li>
                <li><a href="#errors" className="text-neutral-400 hover:text-white transition-colors">Errors</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-3">Core API Reference</h4>
              <ul className="space-y-2.5">
                {ENDPOINTS.map((ep) => (
                  <li key={ep.path + ep.method}>
                    <button
                      onClick={() => {
                        setSelectedEndpoint(ep);
                        setPlaygroundResponse('Click "Send Request" to test api endpoint...');
                      }}
                      className={`text-xs text-left w-full transition-colors font-mono cursor-pointer flex items-center gap-1.5 ${
                        selectedEndpoint.path === ep.path && selectedEndpoint.method === ep.method
                          ? 'text-violet-400 font-bold'
                          : 'text-neutral-400 hover:text-white'
                      }`}
                    >
                      <span className={`text-[8px] font-bold px-1 py-0.5 rounded shrink-0 ${
                        ep.method === 'POST' ? 'bg-violet-600/20 text-violet-400' : 'bg-blue-600/20 text-blue-400'
                      }`}>
                        {ep.method}
                      </span>
                      <span className="truncate">{ep.path}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Column 2: Explanation & API Playground (col-span-5) */}
        <div className="lg:col-span-5 space-y-12 text-left">
          
          {/* Authentication Section */}
          <div id="authentication" className="scroll-mt-28">
            <FadeUp>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-3.5">
                <Key className="w-5 h-5 text-violet-400" /> Authentication
              </h3>
              <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed mb-4">
                All REST API requests require authentication headers. Generate your API key in your Viptant Dashboard settings and include it as a Bearer authorization token:
              </p>
              <div className="p-3 bg-neutral-950 border border-white/5 rounded-lg text-[10px] font-mono text-neutral-400">
                Authorization: Bearer sk_live_...
              </div>
            </FadeUp>
          </div>

          {/* Rate Limits Section */}
          <div id="rate-limits" className="scroll-mt-28">
            <FadeUp>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-3.5">
                <Shield className="w-5 h-5 text-indigo-400" /> Rate Limits
              </h3>
              <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed">
                Standard API rates are limited to <strong className="text-neutral-200">100 requests per minute</strong> per organization. If exceeded, the gateway throws a `429 Too Many Requests` error. Enterprise plans support up to 5,000 requests per minute.
              </p>
            </FadeUp>
          </div>

          {/* Errors Section */}
          <div id="errors" className="scroll-mt-28">
            <FadeUp>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-3.5">
                <AlertTriangle className="w-5 h-5 text-amber-400" /> Errors
              </h3>
              <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed mb-4">
                Viptant uses standard HTTP response codes to denote request outcomes. In general, 2xx codes denote success, 4xx codes indicate missing parameters or key issues, and 5xx codes show database/server issues.
              </p>
            </FadeUp>
          </div>

          {/* Interactive Playground for Selected Endpoint */}
          <FadeUp className="border-t border-white/5 pt-10">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-1.5">
              API Playground <Sparkles className="w-4 h-4 text-violet-400 animate-pulse" />
            </h3>
            <p className="text-xs text-neutral-500 leading-relaxed mb-6">
              Simulate live API calls. Put an API token, set inputs and hit send to test payload outputs.
            </p>

            <div className="p-5 rounded-xl border border-white/10 bg-neutral-950/40 space-y-4 glass">
              <div className="flex items-center gap-2 border-b border-white/5 pb-3">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  selectedEndpoint.method === 'POST' ? 'bg-violet-600/20 text-violet-400' : 'bg-blue-600/20 text-blue-400'
                }`}>
                  {selectedEndpoint.method}
                </span>
                <span className="text-xs font-mono text-white font-semibold">{selectedEndpoint.path}</span>
              </div>

              {/* API Token Input */}
              <div className="space-y-1.5">
                <label className="text-[9px] font-bold text-neutral-400 uppercase tracking-wider">Bearer Token sk_live_... *</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your sk_live_ token to verify..."
                  className="w-full px-3.5 py-2 rounded bg-neutral-900 border border-white/8 text-[11px] text-white placeholder-neutral-700 focus:outline-none focus:border-violet-500 font-mono"
                />
              </div>

              {/* Parameters Display list */}
              <div className="space-y-2.5">
                <span className="text-[9px] font-bold text-neutral-500 uppercase tracking-wider block">Request Parameters</span>
                {selectedEndpoint.params.map((p) => (
                  <div key={p.name} className="flex justify-between items-start border-b border-white/5 pb-2 text-[10px] font-mono last:border-0 last:pb-0">
                    <div>
                      <span className="text-white font-bold">{p.name}</span>
                      <span className="text-neutral-500 text-[8px] ml-1.5 uppercase">{p.type}</span>
                      {p.req && <span className="text-rose-400 text-[8px] ml-1 font-bold">REQUIRED</span>}
                      <p className="text-[9px] text-neutral-400 font-sans mt-0.5">{p.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Send Button */}
              <Button
                variant="violet"
                onClick={handleSendRequest}
                className="w-full h-9 text-xs font-semibold gap-2 mt-4"
                isLoading={playgroundLoading}
              >
                <Terminal className="w-3.5 h-3.5" /> Send Request
              </Button>
            </div>
          </FadeUp>
        </div>

        {/* Column 3: Live Code Snippets & Response (col-span-5) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="sticky top-28 space-y-6">
            
            {/* Request Snippet Block */}
            <div className="space-y-2 text-left">
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Request Sample</span>
                
                <div className="flex gap-2 bg-neutral-950/40 p-1 rounded-lg border border-white/5">
                  {(['curl', 'node'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`px-2.5 py-1 rounded text-[9px] font-bold transition-all cursor-pointer ${
                        activeTab === tab 
                          ? 'bg-neutral-800 text-white border border-white/5' 
                          : 'text-neutral-500 hover:text-neutral-300'
                      }`}
                    >
                      {tab.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <CodeBlock 
                code={activeTab === 'curl' ? selectedEndpoint.curlCode : selectedEndpoint.nodeCode} 
                language={activeTab === 'curl' ? 'bash' : 'javascript'} 
                copyable 
                maxHeight="250px"
              />
            </div>

            {/* Response Console Box */}
            <div className="space-y-2 text-left">
              <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Response Payload</span>
              <CodeBlock 
                code={playgroundResponse} 
                language="json" 
                copyable={playgroundResponse !== 'Click "Send Request" to test api endpoint...'} 
                maxHeight="280px"
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
