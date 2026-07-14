'use client';

import * as React from 'react';
import { Sparkles } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';
import { BrandLogo } from '@/components/ui/brand-logo';

export function AuthLayout({ children }: { children: React.ReactNode }) {
  const { accessToken } = useAuthStore();
  const router = useRouter();

  // Redirect if already logged in
  React.useEffect(() => {
    if (accessToken) {
      router.push('/dashboard');
    }
  }, [accessToken, router]);

  return (
    <div className="min-h-screen bg-black flex text-white font-sans">
      {/* Left Column: Form Content */}
      <div className="flex-1 flex flex-col justify-center px-6 py-12 sm:px-16 lg:px-24 xl:px-32 bg-neutral-950/40 relative z-10">
        <div className="mx-auto w-full max-w-md">
          {/* Brand header */}
          <BrandLogo size="md" onClick={() => router.push('/')} />

          {children}
        </div>
      </div>

      {/* Right Column: Visual Splendor (Apple/Linear style showcase) */}
      <div className="hidden lg:flex flex-1 items-center justify-center bg-black relative overflow-hidden border-l border-white/5">
        {/* Background Grid Pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neutral-900 via-black to-black" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_at_center,black_70%,transparent_100%)]" />

        {/* Ambient Glowing Orbs */}
        <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-violet-600/10 blur-[120px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-indigo-600/10 blur-[160px] animate-pulse" style={{ animationDuration: '6s' }} />

        {/* Core Showcase Card */}
        <div className="relative z-10 max-w-lg p-8 border border-white/10 rounded-2xl bg-neutral-900/40 backdrop-blur-md shadow-2xl flex flex-col gap-6 m-6">
          <div className="inline-flex items-center gap-2 text-violet-400 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-4 h-4" /> Next-Generation AI Partner
          </div>
          
          <h2 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-neutral-100 to-neutral-400">
            Collaborative AI Agents for Enterprise Scale
          </h2>
          
          <p className="text-neutral-400 text-sm leading-relaxed">
            viptant's EAIMOS platform acts as an autonomous AI partner that aligns with your brand guidelines, CRM databases, and historical trends to optimize campaigns in real-time.
          </p>

          <div className="flex flex-col gap-3 mt-4 border-t border-white/5 pt-4">
            <div className="flex items-center gap-3 text-xs text-neutral-400">
              <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
              <span>Multi-tenant SaaS with deep enterprise RBAC integration</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-neutral-400">
              <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
              <span>LangGraph retrieval, CRM workflows, and campaign execution</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-neutral-400">
              <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
              <span>Real-time predictive analytics and optimization engines</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
