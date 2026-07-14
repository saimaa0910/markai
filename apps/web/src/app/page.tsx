import type { Metadata } from 'next';
import { Header } from '@/components/landing/header';
import { HeroSection } from '@/components/landing/hero';
import { TrustSection } from '@/components/landing/trust';
import { PlatformSection } from '@/components/landing/platform';
import { AgentsSection } from '@/components/landing/agents';
import { WorkflowSection } from '@/components/landing/workflow';
import { ShowcaseSection } from '@/components/landing/showcase';
import { IntegrationsSection } from '@/components/landing/integrations';
import { ComparisonSection } from '@/components/landing/comparison';
import { StoriesSection } from '@/components/landing/stories';
import { PricingSection } from '@/components/landing/pricing';
import { FaqSection } from '@/components/landing/faq';
import { CtaSection } from '@/components/landing/cta';
import { Footer } from '@/components/landing/footer';

export const metadata: Metadata = {
  title: 'Viptant — The AI-Native Marketing Operating System',
  description:
    'One intelligent platform to create content, manage CRM, automate campaigns, analyze performance and collaborate with AI Agents. Trusted by 2,000+ marketing teams worldwide.',
};

export default function HomePage() {
  return (
    <div className="relative min-h-screen bg-black text-white selection:bg-violet-500/30 selection:text-white overflow-x-hidden">
      <Header />
      <main>
        <HeroSection />
        <TrustSection />
        <PlatformSection />
        <AgentsSection />
        <WorkflowSection />
        <ShowcaseSection />
        <IntegrationsSection />
        <ComparisonSection />
        <StoriesSection />
        <PricingSection />
        <FaqSection />
        <CtaSection />
      </main>
      <Footer />
    </div>
  );
}
