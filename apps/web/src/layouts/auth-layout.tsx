'use client';

import * as React from 'react';
import { Sparkles } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';
import { BrandLogo } from '@/components/ui/brand-logo';

export function AuthLayout({ children }: { children: React.ReactNode }) {
  const { accessToken } = useAuthStore();
  const router = useRouter();

  React.useEffect(() => {
    if (accessToken) router.push('/dashboard');
  }, [accessToken, router]);

  return (
    <div className="flex min-h-screen bg-background text-foreground font-sans">
      <div className="relative z-10 flex flex-1 flex-col justify-center bg-card/70 px-6 py-12 sm:px-16 lg:px-24 xl:px-32">
        <div className="mx-auto w-full max-w-md">
          <BrandLogo size="md" onClick={() => router.push('/')} />
          {children}
        </div>
      </div>

      <div className="relative hidden flex-1 items-center justify-center overflow-hidden border-l border-border bg-background lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.16),transparent_70%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(15,23,42,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.04)_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_at_center,black_70%,transparent_100%)]" />
        <div className="absolute left-1/4 top-1/4 h-[300px] w-[300px] rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 h-[400px] w-[400px] rounded-full bg-accent/10 blur-[160px]" style={{ animationDuration: '6s' }} />

        <div className="relative z-10 m-6 flex max-w-lg flex-col gap-6 rounded-2xl border border-border bg-card/80 p-8 shadow-card backdrop-blur-md">
          <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
            <Sparkles className="h-4 w-4" /> Next-Generation AI Partner
          </div>
          <h2 className="bg-gradient-to-r from-foreground via-foreground to-muted-foreground bg-clip-text text-3xl font-extrabold tracking-tight text-transparent">
            Collaborative AI Agents for Enterprise Scale
          </h2>
          <p className="text-sm leading-relaxed text-muted-foreground">
            viptant's EAIMOS platform acts as an autonomous AI partner that aligns with your brand guidelines, CRM databases, and historical trends to optimize campaigns in real-time.
          </p>
          <div className="mt-4 flex flex-col gap-3 border-t border-border pt-4">
            <div className="flex items-center gap-3 text-xs text-muted-foreground"><div className="h-1.5 w-1.5 rounded-full bg-primary" /><span>Multi-tenant SaaS with deep enterprise RBAC integration</span></div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground"><div className="h-1.5 w-1.5 rounded-full bg-primary" /><span>LangGraph retrieval, CRM workflows, and campaign execution</span></div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground"><div className="h-1.5 w-1.5 rounded-full bg-primary" /><span>Real-time predictive analytics and optimization engines</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
