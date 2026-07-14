'use client';

import * as React from 'react';
import Link from 'next/link';
import { Sparkles, Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Background grid dot layout */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neutral-900 via-black to-black" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_at_center,black_70%,transparent_100%)]" />

      {/* Ambient Orb */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[350px] h-[350px] rounded-full bg-violet-600/10 blur-[130px]" />

      <div className="relative z-10 max-w-md w-full bg-neutral-900/40 border border-white/10 rounded-2xl p-8 backdrop-blur-md shadow-2xl flex flex-col items-center text-center gap-6">
        <span className="text-6xl font-black bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-indigo-600">
          404
        </span>

        <div className="flex flex-col gap-2">
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center justify-center gap-1.5">
            Page Lost in Orbit <Sparkles className="w-4 h-4 text-violet-400" />
          </h2>
          <p className="text-xs text-neutral-400 leading-relaxed">
            The page you are looking for doesn't exist or has been relocated to another galaxy in the Viptant workspace.
          </p>
        </div>

        <div className="flex gap-3 w-full mt-2">
          <Button
            variant="outline"
            className="flex-1 text-xs gap-2"
            onClick={() => window.history.back()}
          >
            <ArrowLeft className="w-4 h-4" /> Go Back
          </Button>
          <Link href="/dashboard" className="flex-1">
            <Button
              variant="violet"
              className="w-full text-xs gap-2"
            >
              <Home className="w-4 h-4" /> Console Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
