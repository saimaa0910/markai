'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Twitter, Linkedin, Github, ArrowRight } from 'lucide-react';
import { BrandLogo } from '@/components/ui/brand-logo';

const FOOTER_LINKS = {
  Company: ['About', 'Blog', 'Careers', 'Press', 'Contact'],
  Products: ['AI Workspace', 'CRM', 'Campaign Builder', 'Analytics', 'Content Studio', 'Automation'],
  Developers: ['API Docs', 'SDKs', 'Webhooks', 'Changelog', 'Status'],
  Resources: ['Documentation', 'Tutorials', 'Case Studies', 'Community', 'Webinars'],
  Legal: ['Privacy Policy', 'Terms of Service', 'Cookie Policy', 'Security', 'GDPR'],
};

export function Footer() {
  const router = useRouter();
  const [email, setEmail] = React.useState('');

  return (
    <footer className="border-t border-white/6 bg-neutral-950/60">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 mb-16">
          {/* Brand + newsletter */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            {/* Logo */}
            <BrandLogo size="md" onClick={() => router.push('/')} />
            <p className="text-sm text-neutral-500 leading-relaxed max-w-xs">
              The AI-Native Marketing Operating System. Plan, create, automate, and analyze — all in one intelligent workspace.
            </p>

            {/* Newsletter */}
            <div>
              <p className="text-xs font-semibold text-neutral-400 mb-2.5 uppercase tracking-wider">Stay Updated</p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setEmail('');
                }}
                className="flex gap-2"
              >
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="flex-1 px-3 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                />
                <button
                  type="submit"
                  className="px-4 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors flex items-center gap-1"
                >
                  <ArrowRight className="w-4 h-4 text-white" />
                </button>
              </form>
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
                  className="w-9 h-9 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-neutral-400 hover:text-white hover:border-white/20 transition-colors"
                >
                  <Icon className="w-4 h-4" />
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-8">
            {Object.entries(FOOTER_LINKS).map(([category, links]) => (
              <div key={category}>
                <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-4">{category}</h4>
                <ul className="space-y-2.5">
                  {links.map((link) => (
                    <li key={link}>
                      <Link
                        href={link.toLowerCase() === 'contact' ? '/auth/login' : link.toLowerCase() === 'api docs' ? '#' : '#'}
                        className="text-sm text-neutral-600 hover:text-neutral-200 transition-colors"
                      >
                        {link}
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
          <p className="text-xs text-neutral-600">© 2026 Viptant Inc. All rights reserved.</p>
          <div className="flex items-center gap-4 text-xs text-neutral-600">
            <span>SOC 2 Type II</span>
            <span>·</span>
            <span>GDPR Compliant</span>
            <span>·</span>
            <span>99.9% Uptime SLA</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
