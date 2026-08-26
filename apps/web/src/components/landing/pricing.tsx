'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Check, ArrowRight, Sparkles } from 'lucide-react';
import { FadeUp, SectionLabel, GradientHeading } from './primitives';

const PLANS = [
  {
    name: 'Starter',
    price: '$49',
    period: '/month',
    description: 'Perfect for solo marketers and small teams getting started with AI marketing.',
    features: [
      '1 AI agent included',
      'Up to 5 campaigns/month',
      '50K AI tokens/month',
      'Basic CRM (up to 1,000 contacts)',
      'Content Studio (5 assets/month)',
      'Email support',
    ],
    cta: 'Start Free Trial',
    popular: false,
    gradient: '',
    border: 'border-white/8',
  },
  {
    name: 'Growth',
    price: '$149',
    period: '/month',
    description: 'For growing teams ready to scale marketing operations with full AI power.',
    features: [
      '4 AI agents (Content, SEO, Campaign, Analytics)',
      'Unlimited campaigns',
      '500K AI tokens/month',
      'Full CRM (up to 25,000 contacts)',
      'Content Studio (unlimited)',
      'Advanced analytics & reporting',
      'Slack & HubSpot integration',
      'Priority support',
    ],
    cta: 'Start Free Trial',
    popular: true,
    gradient: 'bg-gradient-to-br from-violet-600 to-indigo-600',
    border: 'border-violet-500/30',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large organizations needing custom AI workflows, SSO, and dedicated support.',
    features: [
      'All 8 AI agents',
      'Custom AI model routing',
      'Unlimited tokens',
      'Unlimited contacts & campaigns',
      'Custom integrations & APIs',
      'SSO & RBAC',
      'Dedicated success manager',
      'SLA guarantee',
      'On-premise deployment option',
    ],
    cta: 'Book a Call',
    popular: false,
    gradient: '',
    border: 'border-white/8',
  },
];

function PricingCard({ name, price, period, description, features, cta, popular, gradient, border, index }: (typeof PLANS)[number] & { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className={`relative flex flex-col p-8 rounded-2xl border ${border} ${popular ? 'bg-neutral-950/90 shadow-2xl shadow-violet-500/15 md:-translate-y-2' : 'bg-neutral-950/40'}`}
    >
      {popular && (
        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 text-[10px] font-bold text-white uppercase tracking-widest whitespace-nowrap shadow-lg shadow-violet-500/20">
          Most Popular
        </div>
      )}

      <div className="mb-6">
        <div className={`inline-flex px-3 py-1 rounded-lg text-xs font-semibold mb-3 ${popular ? 'bg-violet-500/15 text-violet-400' : 'bg-neutral-800 text-neutral-400'}`}>
          {name}
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-extrabold text-white">{price}</span>
          {period && <span className="text-neutral-500 text-sm">{period}</span>}
        </div>
        <p className="text-sm text-neutral-500 mt-3 leading-relaxed">{description}</p>
      </div>

      <ul className="space-y-2.5 flex-1 mb-8">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2.5 text-sm text-neutral-400">
            <Check className={`w-4 h-4 mt-0.5 flex-shrink-0 ${popular ? 'text-violet-400' : 'text-emerald-500'}`} />
            {f}
          </li>
        ))}
      </ul>

      <Link
        href={name === 'Enterprise' ? '/auth/login' : '/auth/register'}
        className={`w-full flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 ${
          popular
            ? 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40'
            : 'border border-white/10 bg-white/4 hover:bg-white/8 text-white'
        }`}
      >
        {cta}
        <ArrowRight className="w-4 h-4" />
      </Link>
    </motion.div>
  );
}

export function PricingSection() {
  return (
    <section id="pricing" className="py-28">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <FadeUp>
            <SectionLabel>Simple Pricing</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-2">
              Invest in Your Marketing Intelligence
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="mt-5 text-neutral-500 text-lg max-w-xl mx-auto">
              No hidden fees. No tool overload. One platform, one price, infinite leverage.
            </p>
          </FadeUp>
          <FadeUp delay={0.25}>
            <div className="flex items-center justify-center gap-2 mt-4 text-sm text-neutral-500">
              <Sparkles className="w-4 h-4 text-violet-400" />
              14-day free trial on all plans · No credit card required
            </div>
          </FadeUp>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {PLANS.map((plan, i) => (
            <PricingCard key={plan.name} {...plan} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
