'use client';

import * as React from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

const ThemeContext = React.createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = React.useState<Theme>('dark');
  const [resolvedTheme, setResolvedTheme] = React.useState<'light' | 'dark'>('dark');
  const [mounted, setMounted] = React.useState(false);

  // Initialize from storage or defaults
  React.useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme) {
      setThemeState(savedTheme);
    } else {
      setThemeState('system');
    }
    setMounted(true);
  }, []);

  // Update theme class on root document
  const applyTheme = React.useCallback((nextTheme: Theme) => {
    const root = document.documentElement;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    let activeTheme: 'light' | 'dark' = 'dark';

    if (nextTheme === 'system') {
      activeTheme = mediaQuery.matches ? 'dark' : 'light';
    } else {
      activeTheme = nextTheme;
    }

    if (activeTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    setResolvedTheme(activeTheme);
  }, []);

  // Sync classes when theme state changes
  React.useEffect(() => {
    if (!mounted) return;

    applyTheme(theme);
    localStorage.setItem('theme', theme);

    // Watch for OS system preferences shifts
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleSystemChange = () => {
      if (theme === 'system') {
        applyTheme('system');
      }
    };

    mediaQuery.addEventListener('change', handleSystemChange);
    return () => mediaQuery.removeEventListener('change', handleSystemChange);
  }, [theme, mounted, applyTheme]);

  const setTheme = (nextTheme: Theme) => {
    setThemeState(nextTheme);
  };

  // Prevent flash by avoiding rendering until mounted (or simple fallback)
  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      <div className="transition-colors duration-300 min-h-screen flex flex-col bg-background text-foreground">
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = React.useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be consumed inside a ThemeProvider');
  }
  return context;
}
