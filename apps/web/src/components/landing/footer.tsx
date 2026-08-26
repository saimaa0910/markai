'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Twitter, Linkedin, Github, ArrowRight } from 'lucide-react';
import { BrandLogo } from '@/components/ui/brand-logo';

const FOOTER_SECTIONS = [
  {
    category: 'Company',
    links: [
      { label: 'About', href: '/company/about' },
      { label: 'Blog', href: '/company/blog' },
      { label: 'Careers', href: '/company/careers' },
      { label: 'Press', href: '/company/press' },
      { label: 'Contact', href: '/company/contact' },
    ],
  },
  {
    category: 'Products',
    links: [
      { label: 'AI Workspace', href: '/products/ai-workspace' },
      { label: 'CRM', href: '/products/crm' },
      { label: 'Campaign Builder', href: '/products/campaign-builder' },
      { label: 'Analytics', href: '/products/analytics' },
      { label: 'Content Studio', href: '/products/content-studio' },
      { label: 'Automation', href: '/products/automation' },
    ],
  },
  {
    category: 'Developers',
    links: [
      { label: 'API Docs', href: '/developers/api-docs' },
      { label: 'SDKs', href: '/developers/sdks' },
      { label: 'Webhooks', href: '/developers/webhooks' },
      { label: 'Changelog', href: '/developers/changelog' },
      { label: 'Status', href: '/developers/status' },
    ],
  },
  {
    category: 'Resources',
    links: [
      { label: 'Documentation', href: '/resources/documentation' },
      { label: 'Tutorials', href: '/resources/tutorials' },
      { label: 'Case Studies', href: '/resources/case-studies' },
      { label: 'Community', href: '/resources/community' },
      { label: 'Webinars', href: '/resources/webinars' },
    ],
  },
  {
    category: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '/legal/privacy-policy' },
      { label: 'Terms of Service', href: '/legal/terms' },
      { label: 'Cookie Policy', href: '/legal/cookie-policy' },
      { label: 'Security', href: '/legal/security' },
      { label: 'GDPR', href: '/legal/gdpr' },
    ],
  },
];

export function Footer() {
  const router = useRouter();
  const [email, setEmail] = React.useState('');
  const [subscribed, setSubscribed] = React.useState(false);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setSubscribed(true);
    setEmail('');
  };

  return (
    <footer className="border-t border-white/5 bg-neutral-950/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="mb-16 grid grid-cols-1 gap-12 lg:grid-cols-12">
          <div className="flex flex-col gap-6 lg:col-span-4">
            <BrandLogo size="md" onClick={() => router.push('/')} />
            <p className="max-w-xs text-sm leading-relaxed text-neutral-400">
              The AI-Native Marketing Operating System. Plan, create, automate, and analyze — all in one intelligent workspace.
            </p>

            {/* Newsletter */}
            <div>
              <p className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-neutral-400">Stay Updated</p>
              {subscribed ? (
                <p className="text-xs text-emerald-400 font-medium">Thank you for subscribing to EAIMOS updates!</p>
              ) : (
                <form onSubmit={handleSubscribe} className="flex gap-2">
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="flex-1 rounded-lg border border-white/10 bg-neutral-900 px-3 py-2.5 text-sm text-white placeholder:text-neutral-500 focus:border-violet-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="px-4 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <ArrowRight className="w-4 h-4 text-white" />
                  </button>
                </form>
              )}
            </div>

            {/* Social */}
            <div className="flex items-center gap-3">
              {[
                { Icon: Twitter, href: 'https://twitter.com/viptant' },
                { Icon: Linkedin, href: 'https://linkedin.com/company/viptant' },
                { Icon: Github, href: 'https://github.com/viptant' },
              ].map(({ Icon, href }) => (
                <a 
                  key={href} 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-neutral-900 text-neutral-400 transition-colors hover:border-violet-500/40 hover:text-white"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 md:grid-cols-5 lg:col-span-8">
            {FOOTER_SECTIONS.map((section) => (
              <div key={section.category}>
                <h4 className="mb-4 text-xs font-bold uppercase tracking-widest text-neutral-400">{section.category}</h4>
                <ul className="space-y-2.5">
                  {section.links.map((link) => (
                    <li key={link.label}>
                      <Link
                        href={link.href}
                        className="text-sm text-neutral-400 hover:text-white transition-colors"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-8 border-t border-white/5">
          <p className="text-xs text-neutral-500">© 2026 Viptant Inc. All rights reserved.</p>
          <div className="flex flex-wrap items-center gap-4 text-xs text-neutral-500">
            <Link href="/legal/security" className="hover:text-neutral-300 transition-colors">SOC 2 Type II</Link>
            <span>·</span>
            <Link href="/legal/gdpr" className="hover:text-neutral-300 transition-colors">GDPR Compliant</Link>
            <span>·</span>
            <Link href="/developers/status" className="hover:text-neutral-300 transition-colors">99.9% Uptime SLA</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
