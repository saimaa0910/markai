'use client';

import * as React from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

export function ProgressBar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [animating, setAnimating] = React.useState(false);

  React.useEffect(() => {
    setAnimating(true);
    const timer = setTimeout(() => {
      setAnimating(false);
    }, 450); // Sweeps and fades in 450ms

    return () => clearTimeout(timer);
  }, [pathname, searchParams]);

  return (
    <AnimatePresence>
      {animating && (
        <motion.div
          initial={{ width: '0%', opacity: 1 }}
          animate={{ 
            width: ['0%', '70%', '100%'],
            transition: { duration: 0.45, ease: 'easeInOut' }
          }}
          exit={{ opacity: 0, transition: { duration: 0.15 } }}
          className="fixed top-0 left-0 h-0.5 bg-gradient-to-r from-violet-500 via-purple-500 to-indigo-500 z-50 shadow-[0_0_10px_rgba(139,92,246,0.5)]"
        />
      )}
    </AnimatePresence>
  );
}

export function ProgressBarProvider({ children }: { children: React.ReactNode }) {
  return (
    <>
      <React.Suspense fallback={null}>
        <ProgressBar />
      </React.Suspense>
      {children}
    </>
  );
}
