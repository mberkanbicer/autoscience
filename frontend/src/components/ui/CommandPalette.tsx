'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Search, FileText, Lightbulb, Activity, BookOpen, Settings, Command, Layers, GitBranch, FileSearch, Beaker, GraduationCap, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Command {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  href?: string;
  action?: () => void;
  shortcut?: string;
  category: string;
}

interface CommandPaletteProps {
  projectId?: string;
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ projectId, isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const commands: Command[] = [
    { id: 'ideas', label: 'Ideas', description: 'View and manage research ideas', icon: <Lightbulb size={16} />, href: `/projects/${projectId}/ideas`, category: 'Research', shortcut: 'G I' },
    { id: 'papers', label: 'Papers', description: 'Browse literature corpus', icon: <FileSearch size={16} />, href: `/projects/${projectId}/papers`, category: 'Research', shortcut: 'G P' },
    { id: 'clusters', label: 'Clusters', description: 'View thematic clusters', icon: <Layers size={16} />, href: `/projects/${projectId}/clusters`, category: 'Research', shortcut: 'G C' },
    { id: 'runs', label: 'Research Runs', description: 'View research workflow history', icon: <Activity size={16} />, href: `/projects/${projectId}/runs`, category: 'Workflow', shortcut: 'G R' },
    { id: 'questions', label: 'Questions', description: 'Browse research questions', icon: <MessageSquare size={16} />, href: `/projects/${projectId}/questions`, category: 'Research' },
    { id: 'hypotheses', label: 'Hypotheses', description: 'View generated hypotheses', icon: <GitBranch size={16} />, href: `/projects/${projectId}/hypotheses`, category: 'Research' },
    { id: 'wiki', label: 'Wiki', description: 'Access knowledge base', icon: <BookOpen size={16} />, href: `/projects/${projectId}/wiki`, category: 'Knowledge', shortcut: 'G W' },
    { id: 'manuscripts', label: 'Manuscripts', description: 'Write and export articles', icon: <FileText size={16} />, href: `/projects/${projectId}/manuscripts`, category: 'Article' },
    { id: 'article-studio', label: 'Article Studio', description: 'Full article writing workspace', icon: <GraduationCap size={16} />, href: `/projects/${projectId}/article-studio`, category: 'Article', shortcut: 'G A' },
    { id: 'datasets', label: 'Datasets', description: 'Browse and manage datasets', icon: <Beaker size={16} />, href: `/projects/${projectId}/datasets`, category: 'Experiment' },
    { id: 'settings', label: 'Settings', description: 'Configure project settings', icon: <Settings size={16} />, href: `/projects/${projectId}/settings`, category: 'Project', shortcut: 'G S' },
    { id: 'approvals', label: 'Approvals', description: 'Review pending approval requests', icon: <MessageSquare size={16} />, href: `/projects/${projectId}/approval`, category: 'Workflow' },
    { id: 'team', label: 'Team', description: 'Manage project collaborators', icon: <GraduationCap size={16} />, href: `/projects/${projectId}/team`, category: 'Project' },
  ];

  const filtered = query
    ? commands.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.description.toLowerCase().includes(query.toLowerCase()) ||
        c.category.toLowerCase().includes(query.toLowerCase())
      )
    : commands;

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [query]);

  const execute = useCallback((cmd: Command) => {
    onClose();
    if (cmd.action) {
      cmd.action();
    } else if (cmd.href) {
      router.push(cmd.href);
    }
  }, [onClose, router]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && filtered[selectedIndex]) {
      e.preventDefault();
      execute(filtered[selectedIndex]);
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  // Group filtered results by category
  const grouped = filtered.reduce<Record<string, Command[]>>((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {});

  if (!isOpen) return null;

  let globalIndex = 0;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" onClick={onClose}>
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-xl glass-dark rounded-2xl shadow-2xl border border-white/10 overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/10">
          <Search size={18} className="text-muted-foreground/50 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search commands..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted-foreground/30 font-medium"
          />
          <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono text-muted-foreground/40 bg-white/5 rounded-lg border border-white/10">
            <Command size={12} />K
          </kbd>
        </div>

        {/* Results */}
        <div ref={listRef} className="max-h-[400px] overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground/40 text-sm font-medium">
              No results for &ldquo;{query}&rdquo;
            </div>
          ) : (
            Object.entries(grouped).map(([category, cmds]) => (
              <div key={category}>
                <div className="px-3 py-2 text-[10px] font-black uppercase tracking-widest text-muted-foreground/30">
                  {category}
                </div>
                {cmds.map((cmd) => {
                  const idx = globalIndex++;
                  return (
                    <button
                      key={cmd.id}
                      onClick={() => execute(cmd)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={cn(
                        'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-150 text-left',
                        selectedIndex === idx
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-white/5'
                      )}
                    >
                      <span className={cn(
                        'p-2 rounded-lg shrink-0',
                        selectedIndex === idx ? 'bg-primary/20' : 'bg-white/5'
                      )}>
                        {cmd.icon}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-bold">{cmd.label}</div>
                        <div className="text-[11px] text-muted-foreground/50 truncate">{cmd.description}</div>
                      </div>
                      {cmd.shortcut && (
                        <kbd className="hidden sm:inline-flex text-[10px] font-mono text-muted-foreground/30 bg-white/5 px-2 py-0.5 rounded border border-white/10">
                          {cmd.shortcut}
                        </kbd>
                      )}
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// Hook for keyboard shortcuts
export function useCommandPalette(projectId?: string) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(open => !open);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen]);

  return {
    isOpen,
    setIsOpen,
    CommandPalette: () => <CommandPalette projectId={projectId} isOpen={isOpen} onClose={() => setIsOpen(false)} />,
  };
}
