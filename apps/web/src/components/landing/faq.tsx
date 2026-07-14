'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

const FAQS = [
  {
    q: 'What is Viptant and who is it for?',
    a: 'Viptant is an AI-Native Marketing Operating System designed for marketing teams at B2B companies, SaaS startups, and enterprises. It replaces disconnected tools with one intelligent platform powered by multiple AI agents.',
  },
  {
    q: 'How do the AI agents work?',
    a: 'Each AI agent is a specialized autonomous worker — Content Agent writes copy, SEO Agent manages rankings, Campaign Agent orchestrates channels, and so on. They communicate with each other, share context, and can run tasks overnight without any manual input.',
  },
  {
    q: 'Can I use my existing tools alongside Viptant?',
    a: 'Yes. Viptant integrates natively with 200+ platforms including HubSpot, Salesforce, Google, Meta, LinkedIn, Slack, and Zapier. You can start with partial migration and move fully to Viptant at your own pace.',
  },
  {
    q: 'How does Viptant handle data privacy and security?',
    a: 'Viptant is SOC 2 Type II compliant, GDPR-ready, and offers full data residency controls. Your data is never used to train shared AI models. Enterprise plans include SSO, RBAC, and dedicated VPC deployment options.',
  },
  {
    q: 'What AI models power Viptant?',
    a: 'Viptant routes intelligently across Google Gemini, OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, and your custom fine-tuned models. You can set model preferences per agent or let Viptant auto-route for optimal performance and cost.',
  },
  {
    q: 'Is there a free trial?',
    a: 'Yes — all plans include a 14-day free trial with no credit card required. You get full access to your chosen plan so you can evaluate the platform with real campaigns.',
  },
  {
    q: 'How long does onboarding take?',
    a: "Most teams are live within a day. Viptant's onboarding flow takes 30 minutes. For Enterprise plans, a dedicated success manager runs a structured 1-week onboarding sprint.",
  },
];

function FaqItem({ q, a, index }: { q: string; a: string; index: number }) {
  const [open, setOpen] = React.useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      className="border-b border-white/6 last:border-0"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-4 py-5 text-left cursor-pointer group"
      >
        <span className="text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">
          {q}
        </span>
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.25 }}
          className="w-5 h-5 text-neutral-500 flex-shrink-0"
        >
          <ChevronDown className="w-5 h-5" />
        </motion.div>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <p className="pb-5 text-sm text-neutral-500 leading-relaxed max-w-2xl">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function FaqSection() {
  return (
    <section id="faq" className="py-28 bg-neutral-950/30 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/8 to-transparent" />
      <div className="max-w-3xl mx-auto px-6">
        <div className="text-center mb-14">
          <FadeUp>
            <SectionLabel>FAQ</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Common Questions
            </GradientHeading>
          </FadeUp>
        </div>
        <div>
          {FAQS.map((faq, i) => (
            <FaqItem key={faq.q} {...faq} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
