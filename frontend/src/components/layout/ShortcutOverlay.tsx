'use client';

import { useState } from 'react';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { useArtifact } from '@/lib/ArtifactContext';
import { useRouter, usePathname } from 'next/navigation';
import { X, Keyboard } from 'lucide-react';
import { Button } from '@/components/ui/Button';

const SHORTCUTS = [
  { keys: '?', description: 'Toggle this shortcuts panel' },
  { keys: 'Esc', description: 'Close artifact panel or this overlay' },
  { keys: 'G then P', description: 'Go to projects list' },
  { keys: 'G then S', description: 'Go to settings' },
];

export function ShortcutOverlay() {
  const [open, setOpen] = useState(false);
  const { closeArtifact, isOpen: artifactOpen } = useArtifact();
  const router = useRouter();
  const pathname = usePathname();
  const [pendingG, setPendingG] = useState(false);

  useKeyboardShortcuts([
    {
      key: '?',
      action: () => setOpen((v) => !v),
    },
    {
      key: 'Escape',
      action: () => {
        if (open) setOpen(false);
        else if (artifactOpen) closeArtifact();
      },
    },
    {
      key: 'g',
      action: () => setPendingG(true),
      condition: () => !open,
    },
    {
      key: 'p',
      action: () => {
        if (pendingG) router.push('/projects');
        setPendingG(false);
      },
      condition: () => pendingG,
    },
    {
      key: 's',
      action: () => {
        if (pendingG) router.push('/settings');
        setPendingG(false);
      },
      condition: () => pendingG,
    },
  ]);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 left-4 z-40 p-2 rounded-full glass border border-border/10 text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Keyboard shortcuts"
      >
        <Keyboard size={16} />
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="glass w-full max-w-md rounded-2xl border border-border/10 shadow-2xl p-6 animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Keyboard size={18} />
            Keyboard Shortcuts
          </h2>
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            <X size={18} />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mb-4">Current page: {pathname}</p>
        <ul className="space-y-3">
          {SHORTCUTS.map((item) => (
            <li key={item.keys} className="flex items-center justify-between gap-4">
              <span className="text-sm">{item.description}</span>
              <kbd className="text-[10px] font-mono px-2 py-1 rounded bg-muted border border-border/20">
                {item.keys}
              </kbd>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}