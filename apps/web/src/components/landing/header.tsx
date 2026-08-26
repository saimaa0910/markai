'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Menu, X, ArrowRight, Sparkles } from 'lucide-react';
import { cn } from '@eaimos/shared';
import { Button } from '@/components/ui/button';
import { BrandLogo } from '@/components/ui/brand-logo';
import { ThemeSwitcher } from '@/components/ui/theme-switcher';

export function Header() {
  const router = useRouter();
  const [isScrolled, setIsScrolled] = React.useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { name: 'Platform', href: '#platform' },
    { name: 'AI Agents', href: '#agents' },
    { name: 'Workflow', href: '#workflow' },
    { name: 'Integrations', href: '#integrations' },
    { name: 'Pricing', href: '#pricing' },
    { name: 'FAQ', href: '#faq' }
  ];

  return (
    <>
      <motion.header
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className={cn(
          "fixed top-0 left-0 right-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-200 border-b",
          isScrolled 
            ? "bg-black/80 backdrop-blur-md border-white/10 py-3.5" 
            : "bg-transparent border-transparent py-3.5"
        )}
      >
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          {/* Logo */}
          <BrandLogo size="md" onClick={() => router.push('/')} />

          {/* Desktop Nav Items */}
          <nav className="hidden md:flex items-center gap-6">
            {navItems.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className="text-sm font-medium text-neutral-400 hover:text-white transition-colors"
              >
                {item.name}
              </a>
            ))}
          </nav>

          {/* Right Toolbar */}
          <div className="hidden md:flex items-center gap-3">
            <ThemeSwitcher variant="dropdown" />
            <button className="text-neutral-400 hover:text-white transition-colors cursor-pointer p-2 rounded-lg hover:bg-white/5">
              <Search className="w-4 h-4" />
            </button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => router.push('/auth/login')}
              className="h-9 text-xs"
            >
              Book Demo
            </Button>
            <Button 
              variant="violet" 
              size="sm" 
              onClick={() => router.push('/auth/register')}
              className="h-9 text-xs font-semibold"
            >
              Start Free <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>

          {/* Mobile hamburger menu */}
          <div className="flex items-center gap-2 md:hidden">
            <button className="text-neutral-400 hover:text-white transition-colors cursor-pointer p-2 rounded-lg hover:bg-white/5">
              <Search className="w-4 h-4" />
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-neutral-400 hover:text-white transition-colors cursor-pointer"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="fixed inset-x-0 top-[60px] z-40 bg-neutral-950/95 backdrop-blur-lg border-b border-white/10 p-6 flex flex-col gap-6 md:hidden"
          >
            <nav className="flex flex-col gap-4">
              {navItems.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-base font-semibold text-neutral-300 hover:text-white transition-colors"
                >
                  {item.name}
                </a>
              ))}
            </nav>
            <div className="flex flex-col gap-3 pt-4 border-t border-white/5">
              <Button 
                variant="outline" 
                onClick={() => {
                  setMobileMenuOpen(false);
                  router.push('/auth/login');
                }}
                className="w-full h-10"
              >
                Book Demo
              </Button>
              <Button 
                variant="violet" 
                onClick={() => {
                  setMobileMenuOpen(false);
                  router.push('/auth/register');
                }}
                className="w-full h-10 font-semibold"
              >
                Start Free <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
