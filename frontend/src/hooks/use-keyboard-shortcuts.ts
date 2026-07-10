'use client';

import { useEffect, useRef } from 'react';

interface Shortcut {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  condition?: () => boolean;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  const shortcutsRef = useRef(shortcuts);

  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      shortcutsRef.current.forEach(shortcut => {
        const matchesKey = e.key.toLowerCase() === shortcut.key.toLowerCase();
        const matchesCtrl = shortcut.ctrl === undefined || e.ctrlKey === shortcut.ctrl;
        const matchesMeta = shortcut.meta === undefined || e.metaKey === shortcut.meta;
        const matchesShift = shortcut.shift === undefined || e.shiftKey === shortcut.shift;
        const matchesAlt = shortcut.alt === undefined || e.altKey === shortcut.alt;

        if (matchesKey && matchesCtrl && matchesMeta && matchesShift && matchesAlt) {
          if (!shortcut.condition || shortcut.condition()) {
            e.preventDefault();
            shortcut.action();
          }
        }
      });
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
}