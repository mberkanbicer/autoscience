'use client';

import Link from 'next/link';
import { Menu, FlaskConical } from 'lucide-react';
import { NotificationBell } from './NotificationBell';

interface MobileTopBarProps {
  projectId?: string;
  onMenuClick: () => void;
}

export function MobileTopBar({ projectId, onMenuClick }: MobileTopBarProps) {
  return (
    <header className="lg:hidden sticky top-0 z-30 glass border-b border-border/10 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="p-2 rounded-xl hover:bg-muted transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu size={22} />
        </button>
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-xl flex items-center justify-center">
            <FlaskConical size={16} className="text-stone-900" />
          </div>
          <span className="font-bold text-sm tracking-tight">Autoscience</span>
        </Link>
      </div>
      {projectId && <NotificationBell projectId={projectId} compact />}
    </header>
  );
}