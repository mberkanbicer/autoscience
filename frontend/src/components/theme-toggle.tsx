'use client';

import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="group relative rounded-xl p-2.5 transition-all duration-500 hover:bg-white/10 hover:shadow-lg hover:shadow-primary/5 border border-transparent hover:border-white/10 overflow-hidden"
      aria-label="Toggle theme"
    >
      <div className="relative z-10 transition-transform duration-500 group-hover:rotate-[360deg]">
        {theme === 'dark' ? (
          <Sun className="h-5 w-5 text-warning" />
        ) : (
          <Moon className="h-5 w-5 text-primary" />
        )}
      </div>
      <div className="absolute inset-0 bg-gradient-to-tr from-primary/0 via-primary/5 to-tertiary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
    </button>
  );
}