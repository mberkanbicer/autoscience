'use client';

import { Search } from 'lucide-react';
import { useRef } from 'react';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';

interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
  className?: string;
}

export function SearchBar({ placeholder = "Search...", onSearch, className }: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useKeyboardShortcuts([
    {
      key: 'k',
      meta: true,
      action: () => inputRef.current?.focus(),
    },
  ]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputRef.current?.value ?? '';
    onSearch?.(query);
  };

  return (
    <form onSubmit={handleSubmit} className={className}>
      <div className="relative group">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60 transition-colors group-focus-within:text-primary" />
        <input
          ref={inputRef}
          type="search"
          placeholder={placeholder}
          className="w-full rounded-xl border border-border bg-white/50 backdrop-blur-md pl-11 pr-4 py-2.5 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:bg-white focus:shadow-lg placeholder:text-muted-foreground/40 text-sm font-medium"
        />
        <kbd className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 hidden items-center gap-1 rounded-md border border-border/20 bg-muted/50 backdrop-blur-sm px-2 py-0.5 font-mono text-[10px] opacity-40 sm:inline-flex transition-opacity group-focus-within:opacity-100">
          <span className="text-[10px]">⌘</span>K
        </kbd>
      </div>
    </form>
  );
}