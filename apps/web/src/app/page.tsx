'use client';

import * as React from 'react';
import { Card } from '@eaimos/ui';
import { Shield, Users, Bot, Megaphone, BarChart3, Database, Globe } from 'lucide-react';

export default function Home() {
  const [apiStatus, setApiStatus] = React.useState<'loading' | 'online' | 'offline'>('loading');
  const [apiVersion, setApiVersion] = React.useState<string>('N/A');

  React.useEffect(() => {
    fetch('http://localhost:8000/api/v1/health')
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((data) => {
        if (data.success) {
          setApiStatus('online');
          setApiVersion(data.version || 'v1');
        } else {
          setApiStatus('offline');
        }
      })
      .catch(() => {
        setApiStatus('offline');
      });
  }, []);

  const modules = [
    { name: 'Authentication & RBAC', icon: Shield, desc: 'Secure enterprise SSO, organizations, and fine-grained RBAC.' },
    { name: 'CRM & Contacts', icon: Users, desc: 'Unified leads, contacts, activities, and communication history.' },
    { name: 'AI Platform & Gateway', icon: Bot, desc: 'Multi-model routing, prompt versioning, and LangGraph RAG.' },
    { name: 'Campaign Builder', icon: Megaphone, desc: 'Multi-channel automation, scheduling, and AI copy generation.' },
    { name: 'Analytics & KPIs', icon: BarChart3, desc: 'Real-time performance metrics and predictive modeling.' },
  ];

  return (
    <div className="relative min-h-screen bg-black text-white selection:bg-violet-500/30 selection:text-white">
      {/* Background gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-violet-600/10 rounded-full blur-[128px]" />
        <div className="absolute top-1/2 right-0 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[160px]" />
        <div className="absolute -bottom-40 left-1/3 w-80 h-80 bg-rose-600/5 rounded-full blur-[128px]" />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-20">
        {/* Header */}
        <header className="flex flex-col items-center text-center gap-6 mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/20 bg-violet-500/5 text-violet-400 text-xs font-semibold uppercase tracking-wider">
            <Globe className="w-3.5 h-3.5 animate-spin" /> Production-Ready MVP
          </div>
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-neutral-200 to-neutral-400">
            Enterprise AI Marketing <br className="hidden sm:inline" /> Operating System
          </h1>
          <p className="max-w-2xl text-neutral-400 text-lg sm:text-xl">
            A high-performance modular SaaS platform combining multi-model AI logic, CRM pipelines, and campaigns.
          </p>
        </header>

        {/* Dashboard Status Grid */}
        <section className="mb-20">
          <h2 className="text-xl font-bold tracking-tight text-white mb-6 flex items-center gap-2">
            <Database className="w-5 h-5 text-violet-500" /> System Integration Status
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="flex flex-col justify-between">
              <span className="text-sm text-neutral-400 font-medium">Frontend Web App</span>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-bold">Next.js 16</span>
                <span className="text-xs text-emerald-400 font-semibold px-2 py-0.5 bg-emerald-400/10 rounded-full">ACTIVE</span>
              </div>
            </Card>

            <Card className="flex flex-col justify-between">
              <span className="text-sm text-neutral-400 font-medium">Backend API Gateway</span>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-bold">FastAPI</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  apiStatus === 'online' ? 'text-emerald-400 bg-emerald-400/10' :
                  apiStatus === 'offline' ? 'text-rose-400 bg-rose-400/10' : 'text-yellow-400 bg-yellow-400/10'
                }`}>
                  {apiStatus.toUpperCase()}
                </span>
              </div>
            </Card>

            <Card className="flex flex-col justify-between">
              <span className="text-sm text-neutral-400 font-medium">Database (PGVector)</span>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-bold">PostgreSQL</span>
                <span className="text-xs text-emerald-400 font-semibold px-2 py-0.5 bg-emerald-400/10 rounded-full">CONNECTED</span>
              </div>
            </Card>

            <Card className="flex flex-col justify-between">
              <span className="text-sm text-neutral-400 font-medium">Cache Store</span>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-bold">Redis</span>
                <span className="text-xs text-emerald-400 font-semibold px-2 py-0.5 bg-emerald-400/10 rounded-full">READY</span>
              </div>
            </Card>
          </div>
        </section>

        {/* Modules Grid */}
        <section className="mb-20">
          <h2 className="text-xl font-bold tracking-tight text-white mb-6">Core Operating Modules</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {modules.map((mod, idx) => {
              const Icon = mod.icon;
              return (
                <Card key={idx} className="group relative flex flex-col justify-between transition-all duration-300 hover:-translate-y-1">
                  <div>
                    <div className="inline-flex p-3 rounded-lg border border-white/5 bg-white/5 text-violet-400 mb-6 group-hover:text-violet-300">
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-bold mb-2 group-hover:text-violet-300 transition-colors">{mod.name}</h3>
                    <p className="text-neutral-400 text-sm leading-relaxed">{mod.desc}</p>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 pt-8 flex flex-col sm:flex-row justify-between items-center text-sm text-neutral-500 gap-4">
          <p>© 2026 EAIMOS. All rights reserved.</p>
          <div className="flex gap-6">
            <span className="hover:text-white transition-colors cursor-pointer">API Gateway: Version {apiVersion}</span>
            <span className="hover:text-white transition-colors cursor-pointer">Security: JWT & RBAC Enabled</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
