'use client';

import * as React from 'react';
import { Header } from '@/components/landing/header';
import { Footer } from '@/components/landing/footer';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex flex-col overflow-x-hidden bg-background text-foreground selection:bg-primary/20">
      <Header />
      <main className="flex-1 flex flex-col pt-20">
        {children}
      </main>
      <Footer />
    </div>
  );
}
